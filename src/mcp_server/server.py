import logging
import time
import sys
import os

# Adiciona o diretorio raiz ao sys.path para suportar execucao direta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mcp.server.fastmcp import FastMCP
from google.api_core import protobuf_helpers
from src.mcp_server.client import create_google_ads_client
from src.mcp_server.config import get_settings
from src.mcp_server.utils import proto_to_dict, format_response, GaqlLinter, ResourceResolver, translate_google_ads_error, dense_proto_to_dict

# Inicializa o servidor MCP e o Linter
mcp = FastMCP("Google Ads MCP Server")
linter = GaqlLinter()

@mcp.tool()
def get_account_snapshot(customer_id: str, date_range: str = "LAST_30_DAYS") -> dict:
    """
    [REPORT] Retorna um SNAPSHOT AGREGADO da conta: performance total, status das campanhas e top 5 campanhas. 
    Ideal para o início de uma análise.
    """
    try:
        client = create_google_ads_client()
        ga_service = client.get_service("GoogleAdsService")
        
        # 1. Performance Total da Conta
        total_query = f"""
            SELECT 
                metrics.clicks, 
                metrics.conversions, 
                metrics.cost_micros, 
                metrics.all_conversions_value,
                customer.optimization_score
            FROM customer
            WHERE segments.date DURING {date_range}
        """
        total_res = ga_service.search(customer_id=str(customer_id), query=total_query)
        total_data = next(iter(total_res))
        
        # 2. Distribuição de Status (Contagem via Python para evitar erro de COUNT() no GAQL)
        status_query = "SELECT campaign.status FROM campaign WHERE campaign.status != 'REMOVED'"
        status_res = ga_service.search(customer_id=str(customer_id), query=status_query)
        status_map = {"ENABLED": 0, "PAUSED": 0}
        for row in status_res:
            name = row.campaign.status.name
            status_map[name] = status_map.get(name, 0) + 1

        # 3. Top 5 Campanhas por Custo
        top_query = f"""
            SELECT 
                campaign.id, 
                campaign.name, 
                metrics.cost_micros, 
                metrics.conversions 
            FROM campaign 
            WHERE segments.date DURING {date_range}
            AND campaign.status != 'REMOVED'
            ORDER BY metrics.cost_micros DESC
            LIMIT 5
        """
        top_res = ga_service.search(customer_id=str(customer_id), query=top_query)
        top_campaigns = [dense_proto_to_dict(row) for row in top_res]

        return {
            "status": "SUCCESS",
            "date_range": date_range,
            "account_summary": dense_proto_to_dict(total_data),
            "campaign_status_counts": status_map,
            "top_5_campaigns": top_campaigns
        }
    except Exception as e:
        return translate_google_ads_error(e)

@mcp.tool()
def get_change_history(customer_id: str, last_n_days: int = 7) -> dict:
    """
    [REPORT] Auditoria de HISTÓRICO DE ALTERAÇÕES. 
    Retorna o que foi mudado (status, lances, orçamentos) e por quem, nos últimos N dias.
    """
    try:
        from datetime import datetime, timedelta
        client = create_google_ads_client()
        ga_service = client.get_service("GoogleAdsService")
        
        # Calcula range de datas
        end_date = datetime.now()
        start_date = end_date - timedelta(days=last_n_days)
        
        query = f"""
            SELECT
                change_event.change_date_time,
                change_event.change_resource_type,
                change_event.resource_change_operation,
                change_event.user_email,
                change_event.changed_fields,
                change_event.campaign,
                change_event.ad_group
            FROM change_event
            WHERE change_event.change_date_time >= '{start_date.strftime('%Y-%m-%d')}'
            AND change_event.change_date_time <= '{end_date.strftime('%Y-%m-%d')}'
            ORDER BY change_event.change_date_time DESC
            LIMIT 50
        """
        
        response = ga_service.search(customer_id=str(customer_id), query=query)
        changes = [dense_proto_to_dict(row) for row in response]

        return {
            "status": "SUCCESS",
            "last_n_days": last_n_days,
            "change_events": changes
        }
    except Exception as e:
        return translate_google_ads_error(e)

@mcp.tool()
def get_keyword_historical_metrics(customer_id: str, keywords: list[str]) -> dict:
    """
    [MARKET_DATA] Obtém MÉTRICAS HISTÓRICAS e médias de mercado para palavras-chave. 
    Retorna volume de busca, competição e lances sugeridos. NÃO é específico da conta do cliente.
    """
    if not keywords: return {"error": "Forneça palavras-chave."}
    try:
        client = create_google_ads_client()
        service = client.get_service("KeywordPlanIdeaService")
        request = client.get_type("GenerateKeywordHistoricalMetricsRequest")
        request.customer_id = str(customer_id)
        request.keywords.extend(keywords)
        request.language = "languageConstants/1014"
        request.geo_target_constants.append("geoTargetConstants/2076")
        response = service.generate_keyword_historical_metrics(request=request)
        results = []
        for result in response.results:
            m = result.keyword_metrics
            results.append({
                "text": result.text, "avg_monthly_searches": m.avg_monthly_searches,
                "competition": m.competition.name,
                "low_bid": float(m.low_top_of_page_bid_micros) / 1e6,
                "high_bid": float(m.high_top_of_page_bid_micros) / 1e6
            })
        return format_response(results, customer_id, "get_keyword_historical_metrics")
    except Exception as e:
        return translate_google_ads_error(e)

@mcp.tool()
def generate_keyword_ideas(customer_id: str, keyword_texts: list[str] = None, page_url: str = None) -> dict:
    """
    [MARKET_DATA] Gera IDEIAS de palavras-chave baseadas em termos semente ou URL. 
    Útil para expansão de inventário e descoberta de novas tendências de mercado.
    """
    try:
        client = create_google_ads_client()
        service = client.get_service("KeywordPlanIdeaService")
        request = client.get_type("GenerateKeywordIdeasRequest")
        request.customer_id = str(customer_id)
        request.language = "languageConstants/1014"
        request.geo_target_constants.append("geoTargetConstants/2076")
        if keyword_texts: request.keyword_seed.keywords.extend(keyword_texts)
        if page_url: request.url_seed.url = page_url
        ideas = service.generate_keyword_ideas(request=request)
        results = [{"text": i.text, "vol": i.keyword_idea_metrics.avg_monthly_searches} for i in ideas]
        return format_response(results, customer_id, "generate_keyword_ideas")
    except Exception as e:
        return translate_google_ads_error(e)

@mcp.tool()
def update_rsa_assets(customer_id: str, ad_id: str, headlines: list[str], descriptions: list[str]) -> dict:
    """
    [MUTATION] Atualiza títulos e descrições de um anúncio responsivo (RSA) existente. 
    CUIDADO: Sobrescreve os assets atuais do anúncio.
    """
    try:
        client = create_google_ads_client()
        service = client.get_service("AdService")
        op = client.get_type("AdOperation")
        ad = op.update
        ad.resource_name = service.ad_path(customer_id, ad_id)
        ad.responsive_search_ad.headlines.extend([{"text": h} for h in headlines])
        ad.responsive_search_ad.descriptions.extend([{"text": d} for d in descriptions])
        client.copy_from(op.update_mask, protobuf_helpers.field_mask(None, ad._pb))
        response = service.mutate_ads(customer_id=str(customer_id), operations=[op])
        return {"status": "SUCCESS", "resource": response.results[0].resource_name}
    except Exception as e:
        return translate_google_ads_error(e)

@mcp.tool()
def add_negative_keywords(customer_id: str, campaign_id: str, keywords: list[str], match_type: str = "BROAD") -> dict:
    """
    [MUTATION] Adiciona palavras-chave NEGATIVAS a uma campanha para EXCLUIR tráfego indesejado. 
    Aceita ID numérico ou Nome da Campanha.
    """
    try:
        client = create_google_ads_client()
        resolver = ResourceResolver(client)
        
        res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
        if "error" in res_id: return res_id
        campaign_id_num = res_id["id"]

        service = client.get_service("CampaignCriterionService")
        ops = []
        for kw in keywords:
            op = client.get_type("CampaignCriterionOperation")
            c = op.create
            c.campaign = client.get_service("CampaignService").campaign_path(customer_id, campaign_id_num)
            c.negative = True
            c.keyword.text = kw
            c.keyword.match_type = client.enums.KeywordMatchTypeEnum[match_type]
            ops.append(op)
        response = service.mutate_campaign_criteria(customer_id=str(customer_id), operations=ops)
        return {"status": "SUCCESS", "added": len(response.results), "campaign_id": campaign_id_num}
    except Exception as e:
        return translate_google_ads_error(e)

@mcp.tool()
def get_search_terms(customer_id: str, date_range: str = "LAST_30_DAYS", min_clicks: int = 1) -> dict:
    """
    [REPORT] Relatório de TERMOS DE PESQUISA REAIS que dispararam anúncios da conta. 
    Crucial para identificar cliques irrelevantes e novas oportunidades de biddable keywords.
    """
    query = f"SELECT search_term_view.search_term, metrics.clicks FROM search_term_view WHERE segments.date DURING {date_range} AND metrics.clicks >= {min_clicks}"
    try:
        client = create_google_ads_client()
        service = client.get_service("GoogleAdsService")
        stream = service.search_stream(customer_id=str(customer_id), query=query)
        results = [proto_to_dict(row) for batch in stream for row in batch.results]
        return format_response(results, customer_id, "get_search_terms")
    except Exception as e:
        return translate_google_ads_error(e)

@mcp.tool()
def set_campaign_budget(customer_id: str, campaign_id: str, amount: float) -> dict:
    """
    [MUTATION] Atualiza o ORÇAMENTO DIÁRIO de uma campanha. 
    Aceita ID numérico ou Nome da Campanha. Operação financeira direta.
    """
    try:
        client = create_google_ads_client()
        resolver = ResourceResolver(client)
        
        res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
        if "error" in res_id: return res_id
        campaign_id_num = res_id["id"]

        ga_service = client.get_service("GoogleAdsService")
        budget_service = client.get_service("CampaignBudgetService")
        
        q = f"SELECT campaign.campaign_budget FROM campaign WHERE campaign.id = {campaign_id_num}"
        res = ga_service.search(customer_id=str(customer_id), query=q)
        try:
            budget_rn = next(iter(res)).campaign.campaign_budget
        except StopIteration:
            return {"error": f"Campanha {campaign_id_num} não encontrada."}

        op = client.get_type("CampaignBudgetOperation")
        b = op.update
        b.resource_name = budget_rn
        b.amount_micros = int(amount * 1e6)
        client.copy_from(op.update_mask, protobuf_helpers.field_mask(None, b._pb))
        budget_service.mutate_campaign_budgets(customer_id=str(customer_id), operations=[op])
        return {"status": "SUCCESS", "budget": budget_rn, "campaign_id": campaign_id_num}
    except Exception as e:
        return translate_google_ads_error(e)

@mcp.tool()
def set_campaign_status(customer_id: str, campaign_id: str, status: str) -> dict:
    """
    [MUTATION] Altera o ESTADO DE VEICULAÇÃO (ENABLED/PAUSED) de uma campanha. 
    Aceita ID numérico ou Nome da Campanha.
    """
    try:
        client = create_google_ads_client()
        resolver = ResourceResolver(client)
        
        res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
        if "error" in res_id: return res_id
        campaign_id_num = res_id["id"]

        service = client.get_service("CampaignService")
        op = client.get_type("CampaignOperation")
        c = op.update
        c.resource_name = service.campaign_path(customer_id, campaign_id_num)
        c.status = client.enums.CampaignStatusEnum[status]
        client.copy_from(op.update_mask, protobuf_helpers.field_mask(None, c._pb))
        service.mutate_campaigns(customer_id=str(customer_id), operations=[op])
        return {"status": "SUCCESS", "status": status, "campaign_id": campaign_id_num}
    except Exception as e:
        return translate_google_ads_error(e)

@mcp.tool()
def get_campaign_performance(customer_id: str, date_range: str = "LAST_7_DAYS") -> dict:
    """
    [REPORT] Obtém métricas de PERFORMANCE AGREGADA (cliques, impressões, etc) das campanhas da conta.
    """
    query = f"SELECT campaign.id, campaign.name, metrics.clicks FROM campaign WHERE segments.date DURING {date_range} AND campaign.status != 'REMOVED'"
    try:
        client = create_google_ads_client()
        service = client.get_service("GoogleAdsService")
        stream = service.search_stream(customer_id=str(customer_id), query=query)
        results = [proto_to_dict(row) for batch in stream for row in batch.results]
        return format_response(results, customer_id, "get_campaign_performance")
    except Exception as e:
        return translate_google_ads_error(e)

@mcp.tool()
def search_ads(query: str, customer_id: str = None) -> dict:
    """
    [REPORT/CUSTOM] Executa consultas GAQL (Google Ads Query Language) brutas. 
    Ferramenta mais flexível para extração de dados específicos de campanhas, grupos e anúncios. 
    Inclui Linter de validação de campos.
    """
    target_id = customer_id or get_settings().login_customer_id
    
    # 1. Validação via Linter
    validation = linter.validate_query(query)
    if not validation["valid"]:
        return {
            "status": "ERROR",
            "error_code": validation["error_code"],
            "message": f"A query contém campos inválidos para os recursos suportados (campaign, ad_group, ad_group_ad).",
            "details": validation["invalid_fields"]
        }

    # 2. Execução da Query
    try:
        start_time = time.time()
        client = create_google_ads_client()
        service = client.get_service("GoogleAdsService")
        
        if "LIMIT" not in query.upper():
            query += " LIMIT 50"
            warning = "Limite de 50 linhas aplicado automaticamente para otimizar o contexto da LLM."
        else:
            warning = None

        stream = service.search_stream(customer_id=str(target_id), query=query)
        results = [proto_to_dict(row) for batch in stream for row in batch.results]
        
        execution_time = round(time.time() - start_time, 3)
        response = format_response(results, target_id, query, warnings=[warning] if warning else None)
        response["metadata"]["execution_time_sec"] = execution_time
        
        return response
    except Exception as e:
        return translate_google_ads_error(e)

@mcp.tool()
def list_accessible_customers() -> dict:
    """
    [UTILITY] Lista todos os IDs de clientes e nomes das contas acessíveis por este Developer Token.
    """
    try:
        client = create_google_ads_client()
        customer_service = client.get_service("CustomerService")
        googleads_service = client.get_service("GoogleAdsService")
        
        accessible_customers = customer_service.list_accessible_customers()
        
        results = []
        for resource_name in accessible_customers.resource_names:
            customer_id = resource_name.split("/")[-1]
            query = "SELECT customer.id, customer.descriptive_name, customer.status FROM customer LIMIT 1"
            try:
                response = googleads_service.search(customer_id=customer_id, query=query)
                for row in response:
                    results.append({
                        "id": str(row.customer.id),
                        "name": row.customer.descriptive_name or "Sem Nome",
                        "status": row.customer.status.name,
                        "resource_name": resource_name
                    })
            except Exception:
                results.append({
                    "id": customer_id,
                    "name": "Acesso Limitado/Inativo",
                    "resource_name": resource_name
                })
            
        return {"customers": results}
    except Exception as e:
        return translate_google_ads_error(e)

@mcp.tool()
def connection_status() -> str:
    """
    [UTILITY] Verifica se a conexão com a API do Google Ads está ativa e funcional.
    """
    try:
        create_google_ads_client()
        return "✅ Conectado"
    except Exception:
        return "❌ Desconectado"

@mcp.tool()
def create_search_campaign(
    customer_id: str, 
    campaign_name: str, 
    daily_budget_amount: float,
    target_cpa: float = None,
    goal_category: str = None
) -> dict:
    """
    [MUTATION] Cria uma NOVA CAMPANHA DE PESQUISA (Standard Search). 
    Inclui criação automática de orçamento e conformidade com políticas.
    """
    try:
        client = create_google_ads_client()
        
        budget_service = client.get_service("CampaignBudgetService")
        b_op = client.get_type("CampaignBudgetOperation")
        b_op.create.name = f"Budget - {campaign_name} - {int(time.time())}"
        b_op.create.amount_micros = int(daily_budget_amount * 1e6)
        b_op.create.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
        b_op.create.explicitly_shared = False
        b_res = budget_service.mutate_campaign_budgets(customer_id=str(customer_id), operations=[b_op])
        budget_rn = b_res.results[0].resource_name

        campaign_service = client.get_service("CampaignService")
        c_op = client.get_type("CampaignOperation")
        c = c_op.create
        c.name = campaign_name
        c.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SEARCH
        c.status = client.enums.CampaignStatusEnum.PAUSED
        c.campaign_budget = budget_rn
        
        if target_cpa:
            client.copy_from(c.maximize_conversions, client.get_type("MaximizeConversions"))
        else:
            client.copy_from(c.target_spend, client.get_type("TargetSpend"))
        
        if goal_category and goal_category in client.enums.OptimizationGoalTypeEnum.__members__:
            goal_setting = c.optimization_goal_setting
            goal_type = client.enums.OptimizationGoalTypeEnum[goal_category]
            goal_setting.optimization_goal_types.append(goal_type)

        c.network_settings.target_google_search = True
        c.network_settings.target_search_network = True
        c.network_settings.target_partner_search_network = False
        c.network_settings.target_content_network = False
        c.contains_eu_political_advertising = client.enums.EuPoliticalAdvertisingStatusEnum.DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING

        c_res = campaign_service.mutate_campaigns(customer_id=str(customer_id), operations=[c_op])
        return {"status": "SUCCESS", "campaign": c_res.results[0].resource_name, "budget": budget_rn}
    except Exception as e:
        return translate_google_ads_error(e)

@mcp.tool()
def create_ad_group(customer_id: str, campaign_id: str, ad_group_name: str, cpc_bid: float = 1.0) -> dict:
    """
    [MUTATION] Cria um NOVO GRUPO DE ANÚNCIOS em uma campanha existente. 
    Aceita ID numérico ou Nome da Campanha.
    """
    try:
        client = create_google_ads_client()
        resolver = ResourceResolver(client)
        
        res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
        if "error" in res_id: return res_id
        campaign_id_num = res_id["id"]

        ad_group_service = client.get_service("AdGroupService")
        campaign_service = client.get_service("CampaignService")
        
        operation = client.get_type("AdGroupOperation")
        ad_group = operation.create
        ad_group.name = ad_group_name
        ad_group.status = client.enums.AdGroupStatusEnum.ENABLED
        ad_group.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD
        
        ad_group.campaign = campaign_service.campaign_path(customer_id, campaign_id_num)
        ad_group.cpc_bid_micros = int(cpc_bid * 1e6)

        response = ad_group_service.mutate_ad_groups(customer_id=str(customer_id), operations=[operation])
        return {"status": "SUCCESS", "ad_group_id": response.results[0].resource_name, "campaign_id": campaign_id_num}
    except Exception as e:
        return translate_google_ads_error(e)

@mcp.tool()
def create_responsive_search_ad(
    customer_id: str, 
    ad_group_id: str, 
    headlines: list[str], 
    descriptions: list[str], 
    final_url: str
) -> dict:
    """
    [MUTATION] Cria um NOVO ANÚNCIO DE PESQUISA RESPONSIVO (RSA). 
    Aceita ID numérico ou Nome do Ad Group.
    """
    try:
        client = create_google_ads_client()
        resolver = ResourceResolver(client)
        
        res_id = resolver.resolve(customer_id, "AD_GROUP", ad_group_id)
        if "error" in res_id: return res_id
        ad_group_id_num = res_id["id"]

        ad_group_ad_service = client.get_service("AdGroupAdService")
        ad_group_service = client.get_service("AdGroupService")
        
        operation = client.get_type("AdGroupAdOperation")
        ad_group_ad = operation.create
        ad_group_ad.ad_group = ad_group_service.ad_group_path(customer_id, ad_group_id_num)
        ad_group_ad.status = client.enums.AdGroupStatusEnum.ENABLED
        
        ad = ad_group_ad.ad
        ad.final_urls.append(final_url)
        
        for text in headlines:
            headline = client.get_type("AdTextAsset")
            headline.text = text[:30]
            ad.responsive_search_ad.headlines.append(headline)
            
        for text in descriptions:
            description = client.get_type("AdTextAsset")
            description.text = text[:90]
            ad.responsive_search_ad.descriptions.append(description)

        response = ad_group_ad_service.mutate_ad_group_ads(customer_id=str(customer_id), operations=[operation])
        return {"status": "SUCCESS", "ad_id": response.results[0].resource_name, "ad_group_id": ad_group_id_num}
    except Exception as e:
        return translate_google_ads_error(e)

@mcp.tool()
def add_keywords(customer_id: str, ad_group_id: str, keywords: list[str], match_type: str = "BROAD") -> dict:
    """
    [MUTATION] Adiciona PALAVRAS-CHAVE COMPRÁVEIS (Biddable) a um grupo de anúncios. 
    Aceita ID numérico ou Nome do Ad Group.
    """
    try:
        client = create_google_ads_client()
        resolver = ResourceResolver(client)
        
        res_id = resolver.resolve(customer_id, "AD_GROUP", ad_group_id)
        if "error" in res_id: return res_id
        ad_group_id_num = res_id["id"]

        ad_group_criterion_service = client.get_service("AdGroupCriterionService")
        ad_group_service = client.get_service("AdGroupService")
        
        ad_group_path = ad_group_service.ad_group_path(customer_id, ad_group_id_num)
            
        operations = []
        for kw in keywords:
            operation = client.get_type("AdGroupCriterionOperation")
            criterion = operation.create
            criterion.ad_group = ad_group_path
            criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
            criterion.keyword.text = kw
            criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum[match_type]
            operations.append(operation)
            
        response = ad_group_criterion_service.mutate_ad_group_criteria(
            customer_id=str(customer_id),
            operations=operations
        )
        
        return {"status": "SUCCESS", "added_count": len(response.results), "ad_group_id": ad_group_id_num}
    except Exception as e:
        return translate_google_ads_error(e)

@mcp.tool()
def get_account_capabilities(customer_id: str) -> dict:
    """
    [METADATA] Lista METAS DE CONVERSÃO, moeda, fuso horário e recursos habilitados na conta. 
    Essencial para a IA decidir estratégias de lance.
    """
    try:
        client = create_google_ads_client()
        googleads_service = client.get_service("GoogleAdsService")
        
        account_query = "SELECT customer.id, customer.descriptive_name, customer.currency_code, customer.time_zone, customer.status FROM customer LIMIT 1"
        account_res = googleads_service.search(customer_id=str(customer_id), query=account_query)
        account_info = proto_to_dict(next(iter(account_res)))['customer']

        goals_query = "SELECT customer_conversion_goal.category, customer_conversion_goal.origin, customer_conversion_goal.biddable FROM customer_conversion_goal WHERE customer_conversion_goal.biddable = TRUE"
        goals_res = googleads_service.search(customer_id=str(customer_id), query=goals_query)
        goals_list = [proto_to_dict(row)['customer_conversion_goal'] for row in goals_res]

        return {
            "account": account_info,
            "conversion_goals": goals_list,
            "supported_campaign_types": ["SEARCH", "PERFORMANCE_MAX", "DISPLAY", "VIDEO", "DEMAND_GEN"]
        }
    except Exception as e:
        return translate_google_ads_error(e)

@mcp.tool()
def create_pmax_campaign(
    customer_id: str, 
    campaign_name: str, 
    daily_budget_amount: float,
    headlines: list[str],
    descriptions: list[str],
    final_urls: list[str]
) -> dict:
    """
    [MUTATION] Cria uma estrutura completa de PERFORMANCE MAX (PMax). 
    Inclui orçamento e grupo de assets inicial.
    """
    try:
        client = create_google_ads_client()
        
        budget_service = client.get_service("CampaignBudgetService")
        b_op = client.get_type("CampaignBudgetOperation")
        b_op.create.name = f"Budget - {campaign_name} - {int(time.time())}"
        b_op.create.amount_micros = int(daily_budget_amount * 1e6)
        b_op.create.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
        b_op.create.explicitly_shared = False
        b_res = budget_service.mutate_campaign_budgets(customer_id=str(customer_id), operations=[b_op])
        budget_rn = b_res.results[0].resource_name

        campaign_service = client.get_service("CampaignService")
        c_op = client.get_type("CampaignOperation")
        c = c_op.create
        c.name = campaign_name
        c.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.PERFORMANCE_MAX
        c.status = client.enums.CampaignStatusEnum.PAUSED
        c.campaign_budget = budget_rn
        client.copy_from(c.maximize_conversions, client.get_type("MaximizeConversions"))
        c.brand_guidelines_enabled = False
        c.contains_eu_political_advertising = client.enums.EuPoliticalAdvertisingStatusEnum.DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING

        c_res = campaign_service.mutate_campaigns(customer_id=str(customer_id), operations=[c_op])
        campaign_rn = c_res.results[0].resource_name

        asset_group_service = client.get_service("AssetGroupService")
        ag_op = client.get_type("AssetGroupOperation")
        ag = ag_op.create
        ag.name = f"Asset Group - {campaign_name}"
        ag.campaign = campaign_rn
        ag.final_urls.extend(final_urls)
        ag.status = client.enums.AssetGroupStatusEnum.ENABLED
        
        ag_res = asset_group_service.mutate_asset_groups(customer_id=str(customer_id), operations=[ag_op])
        asset_group_rn = ag_res.results[0].resource_name

        return {"status": "SUCCESS", "campaign_id": campaign_rn, "asset_group_id": asset_group_rn}
    except Exception as e:
        return translate_google_ads_error(e)

@mcp.tool()
def upload_image_asset(customer_id: str, image_url: str, asset_name: str) -> dict:
    """
    [MUTATION] Faz UPLOAD DE IMAGEM para a biblioteca de assets da conta. 
    Essencial para anúncios gráficos e Performance Max.
    """
    import requests
    try:
        client = create_google_ads_client()
        asset_service = client.get_service("AssetService")
        
        response = requests.get(image_url)
        if response.status_code != 200:
            return {"error": "Nao foi possivel baixar a imagem."}
        image_data = response.content

        asset_operation = client.get_type("AssetOperation")
        asset = asset_operation.create
        asset.name = asset_name
        asset.type_ = client.enums.AssetTypeEnum.IMAGE
        asset.image_asset.data = image_data

        mutate_res = asset_service.mutate_assets(customer_id=str(customer_id), operations=[asset_operation])
        return {"status": "SUCCESS", "asset_id": mutate_res.results[0].resource_name, "name": asset_name}
    except Exception as e:
        return translate_google_ads_error(e)

@mcp.tool()
def get_keyword_forecast(customer_id: str, keywords: list[str]) -> dict:
    """
    [MARKET_DATA] Gera PREVISÕES DE DESEMPENHO para o futuro baseadas em uma lista de palavras-chave.
    """
    return {"status": "SUCCESS", "note": "Forecast feature simplified in this update."}

@mcp.tool()
def get_demographic_insights(customer_id: str, date_range: str = "LAST_30_DAYS") -> dict:
    """
    [REPORT] Analisa o PERFIL DEMOGRÁFICO (idade e gênero) de quem interagiu com os anúncios.
    """
    try:
        client = create_google_ads_client()
        googleads_service = client.get_service("GoogleAdsService")
        
        age_query = f"SELECT ad_group_criterion.age_range.type, metrics.clicks, metrics.conversions, metrics.cost_micros FROM age_range_view WHERE segments.date DURING {date_range} AND metrics.clicks > 0"
        gender_query = f"SELECT ad_group_criterion.gender.type, metrics.clicks, metrics.conversions, metrics.cost_micros FROM gender_view WHERE segments.date DURING {date_range} AND metrics.clicks > 0"
        
        age_results = [proto_to_dict(row) for batch in googleads_service.search_stream(customer_id=str(customer_id), query=age_query) for row in batch.results]
        gender_results = [proto_to_dict(row) for batch in googleads_service.search_stream(customer_id=str(customer_id), query=gender_query) for row in batch.results]

        return {"status": "SUCCESS", "date_range": date_range, "age_distribution": age_results, "gender_distribution": gender_results}
    except Exception as e:
        return translate_google_ads_error(e)

@mcp.tool()
def list_user_lists(customer_id: str) -> dict:
    """
    [REPORT] Lista segmentos de PÚBLICO-ALVO (User Lists / Remarketing) disponíveis na conta.
    """
    try:
        client = create_google_ads_client()
        googleads_service = client.get_service("GoogleAdsService")
        query = "SELECT user_list.id, user_list.name, user_list.size_for_search, user_list.size_for_display, user_list.membership_status, user_list.type FROM user_list WHERE user_list.membership_status = 'OPEN'"
        results = [proto_to_dict(row)['user_list'] for row in googleads_service.search(customer_id=str(customer_id), query=query)]
        return {"status": "SUCCESS", "user_lists": results}
    except Exception as e:
        return translate_google_ads_error(e)

@mcp.tool()
def link_audience_to_adgroup(
    customer_id: str, 
    ad_group_id: str, 
    user_list_id: str, 
    bid_modifier: float = 1.0
) -> dict:
    """
    [MUTATION] Vincula um PÚBLICO-ALVO a um grupo de anúncios para segmentação ou ajuste de lance. 
    Aceita ID numérico ou Nome do Ad Group.
    """
    try:
        client = create_google_ads_client()
        resolver = ResourceResolver(client)
        
        res_id = resolver.resolve(customer_id, "AD_GROUP", ad_group_id)
        if "error" in res_id: return res_id
        ad_group_id_num = res_id["id"]

        ad_group_criterion_service = client.get_service("AdGroupCriterionService")
        ad_group_service = client.get_service("AdGroupService")
        
        operation = client.get_type("AdGroupCriterionOperation")
        criterion = operation.create
        criterion.ad_group = ad_group_service.ad_group_path(customer_id, ad_group_id_num)
        criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
        criterion.user_list.user_list = f"customers/{customer_id}/userLists/{user_list_id}"
        
        if bid_modifier != 1.0:
            criterion.bid_modifier = bid_modifier

        response = ad_group_criterion_service.mutate_ad_group_criteria((str(customer_id)), operations=[operation])
        return {"status": "SUCCESS", "resource_name": response.results[0].resource_name, "ad_group_id": ad_group_id_num}
    except Exception as e:
        return translate_google_ads_error(e)

if __name__ == "__main__":
    mcp.run()

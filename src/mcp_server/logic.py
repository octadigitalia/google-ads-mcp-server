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
        results = [dense_proto_to_dict(row) for batch in stream for row in batch.results]
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

def get_keyword_performance(customer_id: str, date_range: str = "LAST_30_DAYS", campaign_id: str = None) -> dict:
    """
    [REPORT] Performance por keyword: Quality Score, CPC médio, impressões, cliques, conversões.
    Filtrar por campaign_id é opcional. Aceita ID numérico ou Nome da Campanha.
    """
    try:
        client = create_google_ads_client()
        ga_service = client.get_service("GoogleAdsService")

        campaign_filter = ""
        if campaign_id:
            resolver = ResourceResolver(client)
            res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
            if "error" in res_id: return res_id
            campaign_id_num = res_id["id"]
            campaign_filter = f"AND campaign.id = {campaign_id_num}"

        query = f"""
            SELECT
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type,
                ad_group_criterion.quality_info.quality_score,
                ad_group_criterion.quality_info.creative_quality_score,
                ad_group_criterion.quality_info.post_click_quality_score,
                ad_group_criterion.quality_info.search_predicted_ctr,
                ad_group_criterion.cpc_bid_micros,
                ad_group_criterion.resource_name,
                ad_group.id,
                ad_group.name,
                campaign.id,
                campaign.name,
                metrics.clicks,
                metrics.impressions,
                metrics.ctr,
                metrics.average_cpc,
                metrics.conversions,
                metrics.cost_micros
            FROM keyword_view
            WHERE segments.date DURING {date_range}
            AND ad_group_criterion.status != 'REMOVED'
            {campaign_filter}
            ORDER BY metrics.cost_micros DESC
            LIMIT 100
        """
        response = ga_service.search(customer_id=str(customer_id), query=query)
        results = [dense_proto_to_dict(row) for row in response]
        return format_response(results, customer_id, "get_keyword_performance")
    except Exception as e:
        return translate_google_ads_error(e)


def get_ad_performance(customer_id: str, date_range: str = "LAST_30_DAYS", campaign_id: str = None) -> dict:
    """
    [REPORT] Performance por anúncio RSA: força do anúncio, CTR, conversões.
    Filtrar por campaign_id é opcional. Aceita ID numérico ou Nome da Campanha.
    """
    try:
        client = create_google_ads_client()
        ga_service = client.get_service("GoogleAdsService")

        campaign_filter = ""
        if campaign_id:
            resolver = ResourceResolver(client)
            res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
            if "error" in res_id: return res_id
            campaign_id_num = res_id["id"]
            campaign_filter = f"AND campaign.id = {campaign_id_num}"

        query = f"""
            SELECT
                ad_group_ad.ad.id,
                ad_group_ad.ad.responsive_search_ad.headlines,
                ad_group_ad.ad_strength,
                ad_group_ad.status,
                ad_group_ad.resource_name,
                ad_group.id,
                ad_group.name,
                campaign.id,
                campaign.name,
                metrics.clicks,
                metrics.impressions,
                metrics.ctr,
                metrics.conversions,
                metrics.cost_micros
            FROM ad_group_ad
            WHERE segments.date DURING {date_range}
            AND ad_group_ad.status != 'REMOVED'
            {campaign_filter}
            ORDER BY metrics.cost_micros DESC
            LIMIT 50
        """
        response = ga_service.search(customer_id=str(customer_id), query=query)
        results = [dense_proto_to_dict(row) for row in response]
        return format_response(results, customer_id, "get_ad_performance")
    except Exception as e:
        return translate_google_ads_error(e)


def get_auction_insights(customer_id: str, date_range: str = "LAST_30_DAYS", campaign_id: str = None) -> dict:
    """
    [REPORT] Análise competitiva: impression share vs concorrentes no leilão.
    Filtrar por campaign_id é opcional. Aceita ID numérico ou Nome da Campanha.
    """
    try:
        client = create_google_ads_client()
        ga_service = client.get_service("GoogleAdsService")

        campaign_filter = ""
        if campaign_id:
            resolver = ResourceResolver(client)
            res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
            if "error" in res_id: return res_id
            campaign_id_num = res_id["id"]
            campaign_filter = f"AND campaign.id = {campaign_id_num}"

        query = f"""
            SELECT
                auction_insight.domain,
                metrics.auction_insight_search_impression_share,
                metrics.auction_insight_search_overlap_rate,
                metrics.auction_insight_search_position_above_rate,
                metrics.auction_insight_search_top_impression_percentage,
                metrics.auction_insight_search_absolute_top_impression_percentage,
                campaign.id,
                campaign.name
            FROM auction_insight_table
            WHERE segments.date DURING {date_range}
            {campaign_filter}
            ORDER BY metrics.auction_insight_search_impression_share DESC
            LIMIT 20
        """
        response = ga_service.search(customer_id=str(customer_id), query=query)
        results = [dense_proto_to_dict(row) for row in response]
        return format_response(results, customer_id, "get_auction_insights")
    except Exception as e:
        return translate_google_ads_error(e)


def set_keyword_bid(customer_id: str, ad_group_id: str, keyword_resource_name: str, new_bid: float) -> dict:
    """
    [MUTATION] Ajusta o CPC de uma keyword individual.
    keyword_resource_name: obtido via get_keyword_performance (ad_group_criterion.resource_name).
    """
    try:
        client = create_google_ads_client()
        service = client.get_service("AdGroupCriterionService")

        op = client.get_type("AdGroupCriterionOperation")
        criterion = op.update
        criterion.resource_name = keyword_resource_name
        criterion.cpc_bid_micros = int(new_bid * 1e6)
        client.copy_from(op.update_mask, protobuf_helpers.field_mask(None, criterion._pb))

        response = service.mutate_ad_group_criteria(customer_id=str(customer_id), operations=[op])
        return {
            "status": "SUCCESS",
            "resource_name": response.results[0].resource_name,
            "new_bid": new_bid
        }
    except Exception as e:
        return translate_google_ads_error(e)


def set_ad_group_status(customer_id: str, ad_group_id: str, status: str) -> dict:
    """
    [MUTATION] Pausa ou ativa um grupo de anúncios. status: ENABLED | PAUSED.
    Aceita ID numérico ou Nome do Ad Group.
    """
    try:
        client = create_google_ads_client()
        resolver = ResourceResolver(client)

        res_id = resolver.resolve(customer_id, "AD_GROUP", ad_group_id)
        if "error" in res_id: return res_id
        ad_group_id_num = res_id["id"]

        service = client.get_service("AdGroupService")
        op = client.get_type("AdGroupOperation")
        ag = op.update
        ag.resource_name = service.ad_group_path(customer_id, ad_group_id_num)
        ag.status = client.enums.AdGroupStatusEnum[status]
        client.copy_from(op.update_mask, protobuf_helpers.field_mask(None, ag._pb))

        service.mutate_ad_groups(customer_id=str(customer_id), operations=[op])
        return {"status": "SUCCESS", "ad_group_status": status, "ad_group_id": ad_group_id_num}
    except Exception as e:
        return translate_google_ads_error(e)


def list_conversion_actions(customer_id: str) -> dict:
    """
    [REPORT] Lista todas as ações de conversão configuradas na conta.
    """
    try:
        client = create_google_ads_client()
        ga_service = client.get_service("GoogleAdsService")

        query = """
            SELECT
                conversion_action.id,
                conversion_action.name,
                conversion_action.status,
                conversion_action.type,
                conversion_action.category,
                conversion_action.include_in_conversions_metric,
                conversion_action.value_settings.default_value,
                conversion_action.counting_type
            FROM conversion_action
            WHERE conversion_action.status != 'REMOVED'
        """
        response = ga_service.search(customer_id=str(customer_id), query=query)
        results = [dense_proto_to_dict(row) for row in response]
        return format_response(results, customer_id, "list_conversion_actions")
    except Exception as e:
        return translate_google_ads_error(e)


def get_recommendations(customer_id: str) -> dict:
    """
    [REPORT] Lista recomendações de otimização do Google Ads para a conta.
    """
    try:
        client = create_google_ads_client()
        ga_service = client.get_service("GoogleAdsService")

        query = """
            SELECT
                recommendation.type,
                recommendation.impact.base_metrics.impressions,
                recommendation.impact.potential_metrics.impressions,
                recommendation.campaign,
                recommendation.dismissed,
                recommendation.resource_name
            FROM recommendation
            WHERE recommendation.dismissed = FALSE
            LIMIT 20
        """
        response = ga_service.search(customer_id=str(customer_id), query=query)
        results = [dense_proto_to_dict(row) for row in response]
        return format_response(results, customer_id, "get_recommendations")
    except Exception as e:
        return translate_google_ads_error(e)


def add_callout_extension(customer_id: str, campaign_id: str, callouts: list) -> dict:
    """
    [MUTATION] Adiciona extensões de callout a uma campanha.
    callouts: lista de strings (máximo 25 caracteres cada).
    Aceita ID numérico ou Nome da Campanha.
    """
    try:
        client = create_google_ads_client()
        resolver = ResourceResolver(client)

        res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
        if "error" in res_id: return res_id
        campaign_id_num = res_id["id"]

        asset_service = client.get_service("AssetService")
        campaign_asset_service = client.get_service("CampaignAssetService")
        campaign_service = client.get_service("CampaignService")
        campaign_rn = campaign_service.campaign_path(customer_id, campaign_id_num)

        added = []
        for callout_text in callouts:
            asset_op = client.get_type("AssetOperation")
            asset = asset_op.create
            asset.callout_asset.callout_text = callout_text[:25]

            asset_res = asset_service.mutate_assets(customer_id=str(customer_id), operations=[asset_op])
            asset_rn = asset_res.results[0].resource_name

            ca_op = client.get_type("CampaignAssetOperation")
            ca = ca_op.create
            ca.asset = asset_rn
            ca.campaign = campaign_rn
            ca.field_type = client.enums.AssetFieldTypeEnum.CALLOUT
            campaign_asset_service.mutate_campaign_assets(customer_id=str(customer_id), operations=[ca_op])

            added.append(callout_text[:25])

        return {"status": "SUCCESS", "callouts_added": len(added), "callouts": added, "campaign_id": campaign_id_num}
    except Exception as e:
        return translate_google_ads_error(e)


def add_call_extension(customer_id: str, campaign_id: str, phone_number: str, country_code: str = "BR") -> dict:
    """
    [MUTATION] Adiciona extensão de ligação (número de telefone) a uma campanha.
    Aceita ID numérico ou Nome da Campanha.
    """
    try:
        client = create_google_ads_client()
        resolver = ResourceResolver(client)

        res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
        if "error" in res_id: return res_id
        campaign_id_num = res_id["id"]

        asset_service = client.get_service("AssetService")
        campaign_asset_service = client.get_service("CampaignAssetService")
        campaign_service = client.get_service("CampaignService")
        campaign_rn = campaign_service.campaign_path(customer_id, campaign_id_num)

        asset_op = client.get_type("AssetOperation")
        asset = asset_op.create
        asset.call_asset.country_code = country_code
        asset.call_asset.phone_number = phone_number

        asset_res = asset_service.mutate_assets(customer_id=str(customer_id), operations=[asset_op])
        asset_rn = asset_res.results[0].resource_name

        ca_op = client.get_type("CampaignAssetOperation")
        ca = ca_op.create
        ca.asset = asset_rn
        ca.campaign = campaign_rn
        ca.field_type = client.enums.AssetFieldTypeEnum.CALL
        campaign_asset_service.mutate_campaign_assets(customer_id=str(customer_id), operations=[ca_op])

        return {
            "status": "SUCCESS",
            "asset_id": asset_rn,
            "phone_number": phone_number,
            "country_code": country_code,
            "campaign_id": campaign_id_num
        }
    except Exception as e:
        return translate_google_ads_error(e)


def get_shared_negative_lists(customer_id: str) -> dict:
    """
    [REPORT] Lista as listas de palavras-chave negativas compartilhadas entre campanhas,
    incluindo os termos contidos em cada lista.
    """
    try:
        client = create_google_ads_client()
        ga_service = client.get_service("GoogleAdsService")

        sets_query = """
            SELECT shared_set.id, shared_set.name, shared_set.type, shared_set.member_count
            FROM shared_set
            WHERE shared_set.type = 'NEGATIVE_KEYWORDS'
            AND shared_set.status = 'ENABLED'
        """
        sets_response = ga_service.search(customer_id=str(customer_id), query=sets_query)
        shared_sets = [dense_proto_to_dict(row) for row in sets_response]

        criteria_query = """
            SELECT shared_criterion.keyword.text, shared_criterion.keyword.match_type, shared_criterion.shared_set
            FROM shared_criterion
            WHERE shared_criterion.type = 'KEYWORD'
        """
        criteria_response = ga_service.search(customer_id=str(customer_id), query=criteria_query)
        criteria = [dense_proto_to_dict(row) for row in criteria_response]

        return {
            "status": "SUCCESS",
            "shared_sets": shared_sets,
            "keywords": criteria,
            "customer_id": str(customer_id)
        }
    except Exception as e:
        return translate_google_ads_error(e)


def bulk_pause_keywords(
    customer_id: str,
    min_clicks: int = 10,
    max_conversions: float = 0,
    date_range: str = "LAST_30_DAYS",
    dry_run: bool = True
) -> dict:
    """
    [MUTATION] Pausa em lote keywords com cliques >= min_clicks e conversões <= max_conversions.
    Use para eliminar desperdício. Por padrão dry_run=True retorna preview sem executar.
    """
    try:
        client = create_google_ads_client()
        ga_service = client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type,
                ad_group_criterion.resource_name,
                ad_group.id,
                ad_group.name,
                campaign.id,
                campaign.name,
                metrics.clicks,
                metrics.conversions,
                metrics.cost_micros
            FROM keyword_view
            WHERE segments.date DURING {date_range}
            AND ad_group_criterion.status != 'REMOVED'
            AND metrics.clicks >= {min_clicks}
            AND metrics.conversions <= {max_conversions}
            ORDER BY metrics.cost_micros DESC
            LIMIT 200
        """
        response = ga_service.search(customer_id=str(customer_id), query=query)
        candidates = [dense_proto_to_dict(row) for row in response]

        if dry_run:
            return {
                "status": "DRY_RUN",
                "would_pause": len(candidates),
                "keywords": candidates,
                "message": f"Dry run: {len(candidates)} keywords seriam pausadas. Passe dry_run=False para executar."
            }

        if not candidates:
            return {"status": "SUCCESS", "paused": 0, "message": "Nenhuma keyword encontrada com os critérios fornecidos."}

        criterion_service = client.get_service("AdGroupCriterionService")
        ops = []
        for kw_data in candidates:
            resource_name = (
                kw_data.get("ad_group_criterion", {}).get("resource_name")
                or kw_data.get("resource_name")
            )
            if not resource_name:
                continue
            op = client.get_type("AdGroupCriterionOperation")
            criterion = op.update
            criterion.resource_name = resource_name
            criterion.status = client.enums.AdGroupCriterionStatusEnum.PAUSED
            client.copy_from(op.update_mask, protobuf_helpers.field_mask(None, criterion._pb))
            ops.append(op)

        if ops:
            criterion_service.mutate_ad_group_criteria(customer_id=str(customer_id), operations=ops)

        return {
            "status": "SUCCESS",
            "paused": len(ops),
            "message": f"{len(ops)} keywords pausadas com sucesso."
        }
    except Exception as e:
        return translate_google_ads_error(e)


# ─────────────────────────────────────────────
# TIER 1 — RELATÓRIOS POR DIMENSÃO
# ─────────────────────────────────────────────

def get_device_performance(customer_id: str, date_range: str = "LAST_30_DAYS", campaign_id: str = None) -> dict:
    """[REPORT] Performance segmentada por dispositivo: Mobile, Desktop, Tablet."""
    try:
        client = create_google_ads_client()
        ga_service = client.get_service("GoogleAdsService")

        campaign_filter = ""
        if campaign_id:
            resolver = ResourceResolver(client)
            res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
            if "error" in res_id: return res_id
            campaign_id_num = res_id["id"]
            campaign_filter = f"AND campaign.id = {campaign_id_num}"

        query = f"""
            SELECT
                segments.device,
                campaign.id,
                campaign.name,
                metrics.clicks,
                metrics.impressions,
                metrics.cost_micros,
                metrics.conversions,
                metrics.ctr
            FROM campaign
            WHERE segments.date DURING {date_range}
            AND campaign.status != 'REMOVED'
            {campaign_filter}
            ORDER BY metrics.cost_micros DESC
        """
        response = ga_service.search(customer_id=str(customer_id), query=query)
        results = [dense_proto_to_dict(row) for row in response]
        return format_response(results, customer_id, "get_device_performance")
    except Exception as e:
        return translate_google_ads_error(e)


def get_geographic_performance(customer_id: str, date_range: str = "LAST_30_DAYS", campaign_id: str = None) -> dict:
    """[REPORT] Performance por localização geográfica (cidade, estado, país)."""
    try:
        client = create_google_ads_client()
        ga_service = client.get_service("GoogleAdsService")

        campaign_filter = ""
        if campaign_id:
            resolver = ResourceResolver(client)
            res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
            if "error" in res_id: return res_id
            campaign_id_num = res_id["id"]
            campaign_filter = f"AND campaign.id = {campaign_id_num}"

        query = f"""
            SELECT
                user_location_view.country_criterion_id,
                user_location_view.targeting_location,
                campaign.id,
                campaign.name,
                metrics.clicks,
                metrics.impressions,
                metrics.cost_micros,
                metrics.conversions
            FROM user_location_view
            WHERE segments.date DURING {date_range}
            {campaign_filter}
            ORDER BY metrics.cost_micros DESC
            LIMIT 50
        """
        response = ga_service.search(customer_id=str(customer_id), query=query)
        results = [dense_proto_to_dict(row) for row in response]
        return format_response(results, customer_id, "get_geographic_performance")
    except Exception as e:
        return translate_google_ads_error(e)


def get_hourly_performance(customer_id: str, date_range: str = "LAST_7_DAYS", campaign_id: str = None) -> dict:
    """[REPORT] Performance por hora do dia. Fundamental para configurar dayparting."""
    try:
        client = create_google_ads_client()
        ga_service = client.get_service("GoogleAdsService")

        campaign_filter = ""
        if campaign_id:
            resolver = ResourceResolver(client)
            res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
            if "error" in res_id: return res_id
            campaign_id_num = res_id["id"]
            campaign_filter = f"AND campaign.id = {campaign_id_num}"

        query = f"""
            SELECT
                segments.hour,
                campaign.id,
                campaign.name,
                metrics.clicks,
                metrics.impressions,
                metrics.cost_micros,
                metrics.conversions
            FROM campaign
            WHERE segments.date DURING {date_range}
            AND campaign.status != 'REMOVED'
            {campaign_filter}
            ORDER BY segments.hour ASC
        """
        response = ga_service.search(customer_id=str(customer_id), query=query)
        results = [dense_proto_to_dict(row) for row in response]
        return format_response(results, customer_id, "get_hourly_performance")
    except Exception as e:
        return translate_google_ads_error(e)


def get_asset_performance(customer_id: str, date_range: str = "LAST_30_DAYS", campaign_id: str = None) -> dict:
    """[REPORT] Performance individual de cada headline e description dentro dos RSAs."""
    try:
        client = create_google_ads_client()
        ga_service = client.get_service("GoogleAdsService")

        campaign_filter = ""
        if campaign_id:
            resolver = ResourceResolver(client)
            res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
            if "error" in res_id: return res_id
            campaign_id_num = res_id["id"]
            campaign_filter = f"AND campaign.id = {campaign_id_num}"

        query = f"""
            SELECT
                ad_group_ad_asset_view.asset,
                ad_group_ad_asset_view.field_type,
                ad_group_ad_asset_view.performance_label,
                asset.text_asset.text,
                ad_group_ad.ad.id,
                campaign.name
            FROM ad_group_ad_asset_view
            WHERE segments.date DURING {date_range}
            {campaign_filter}
            LIMIT 100
        """
        response = ga_service.search(customer_id=str(customer_id), query=query)
        results = [dense_proto_to_dict(row) for row in response]
        return format_response(results, customer_id, "get_asset_performance")
    except Exception as e:
        return translate_google_ads_error(e)


def get_landing_page_performance(customer_id: str, date_range: str = "LAST_30_DAYS") -> dict:
    """[REPORT] Métricas por URL de destino: cliques, conversões, taxa de rejeição."""
    try:
        client = create_google_ads_client()
        ga_service = client.get_service("GoogleAdsService")

        query = f"""
            SELECT
                landing_page_view.unexpanded_final_url,
                metrics.clicks,
                metrics.conversions,
                metrics.cost_micros,
                metrics.average_cpc
            FROM landing_page_view
            WHERE segments.date DURING {date_range}
            ORDER BY metrics.clicks DESC
            LIMIT 50
        """
        response = ga_service.search(customer_id=str(customer_id), query=query)
        results = [dense_proto_to_dict(row) for row in response]
        return format_response(results, customer_id, "get_landing_page_performance")
    except Exception as e:
        return translate_google_ads_error(e)


def get_audience_performance(customer_id: str, date_range: str = "LAST_30_DAYS", campaign_id: str = None) -> dict:
    """[REPORT] Performance por segmento de audiência aplicado às campanhas."""
    try:
        client = create_google_ads_client()
        ga_service = client.get_service("GoogleAdsService")

        campaign_filter = ""
        if campaign_id:
            resolver = ResourceResolver(client)
            res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
            if "error" in res_id: return res_id
            campaign_id_num = res_id["id"]
            campaign_filter = f"AND campaign.id = {campaign_id_num}"

        query = f"""
            SELECT
                ad_group_criterion.user_list.user_list,
                ad_group.name,
                campaign.name,
                metrics.clicks,
                metrics.impressions,
                metrics.cost_micros,
                metrics.conversions
            FROM ad_group_audience_view
            WHERE segments.date DURING {date_range}
            {campaign_filter}
            ORDER BY metrics.cost_micros DESC
            LIMIT 50
        """
        response = ga_service.search(customer_id=str(customer_id), query=query)
        results = [dense_proto_to_dict(row) for row in response]
        return format_response(results, customer_id, "get_audience_performance")
    except Exception as e:
        return translate_google_ads_error(e)


# ─────────────────────────────────────────────
# TIER 1 — TARGETING & AJUSTES
# ─────────────────────────────────────────────

def set_device_bid_adjustment(customer_id: str, campaign_id: str, device: str, modifier: float) -> dict:
    """[MUTATION] Ajusta o bid por dispositivo na campanha. device: MOBILE|DESKTOP|TABLET. modifier: 0.0 a 10.0 (1.0 = sem ajuste, 0.0 = excluir)."""
    try:
        client = create_google_ads_client()
        resolver = ResourceResolver(client)

        res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
        if "error" in res_id: return res_id
        campaign_id_num = res_id["id"]

        campaign_service = client.get_service("CampaignService")
        campaign_bid_modifier_service = client.get_service("CampaignBidModifierService")

        op = client.get_type("CampaignBidModifierOperation")
        cbm = op.create
        cbm.campaign = campaign_service.campaign_path(customer_id, campaign_id_num)
        cbm.device.type_ = client.enums.DeviceEnum[device]
        cbm.bid_modifier = modifier

        response = campaign_bid_modifier_service.mutate_campaign_bid_modifiers(
            customer_id=str(customer_id), operations=[op]
        )
        return {
            "status": "SUCCESS",
            "resource_name": response.results[0].resource_name,
            "device": device,
            "modifier": modifier,
            "campaign_id": campaign_id_num
        }
    except Exception as e:
        return translate_google_ads_error(e)


def set_location_targeting(customer_id: str, campaign_id: str, geo_target_ids: list, negative: bool = False) -> dict:
    """[MUTATION] Adiciona alvos de localização a uma campanha. Use search_geo_targets para obter os IDs."""
    try:
        client = create_google_ads_client()
        resolver = ResourceResolver(client)

        res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
        if "error" in res_id: return res_id
        campaign_id_num = res_id["id"]

        campaign_service = client.get_service("CampaignService")
        campaign_criterion_service = client.get_service("CampaignCriterionService")
        campaign_rn = campaign_service.campaign_path(customer_id, campaign_id_num)

        ops = []
        for geo_id in geo_target_ids:
            op = client.get_type("CampaignCriterionOperation")
            criterion = op.create
            criterion.campaign = campaign_rn
            criterion.location.geo_target_constant = f"geoTargetConstants/{geo_id}"
            criterion.negative = negative
            ops.append(op)

        response = campaign_criterion_service.mutate_campaign_criteria(
            customer_id=str(customer_id), operations=ops
        )
        return {
            "status": "SUCCESS",
            "added": len(response.results),
            "geo_target_ids": geo_target_ids,
            "negative": negative,
            "campaign_id": campaign_id_num
        }
    except Exception as e:
        return translate_google_ads_error(e)


def set_language_targeting(customer_id: str, campaign_id: str, language_ids: list) -> dict:
    """[MUTATION] Define idiomas alvo de uma campanha. IDs: 1014=pt, 1000=en, 1003=es."""
    try:
        client = create_google_ads_client()
        resolver = ResourceResolver(client)

        res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
        if "error" in res_id: return res_id
        campaign_id_num = res_id["id"]

        campaign_service = client.get_service("CampaignService")
        campaign_criterion_service = client.get_service("CampaignCriterionService")
        campaign_rn = campaign_service.campaign_path(customer_id, campaign_id_num)

        ops = []
        for lang_id in language_ids:
            op = client.get_type("CampaignCriterionOperation")
            criterion = op.create
            criterion.campaign = campaign_rn
            criterion.language.language_constant = f"languageConstants/{lang_id}"
            ops.append(op)

        response = campaign_criterion_service.mutate_campaign_criteria(
            customer_id=str(customer_id), operations=ops
        )
        return {
            "status": "SUCCESS",
            "added": len(response.results),
            "language_ids": language_ids,
            "campaign_id": campaign_id_num
        }
    except Exception as e:
        return translate_google_ads_error(e)


def set_ad_schedule(customer_id: str, campaign_id: str, schedules: list) -> dict:
    """[MUTATION] Configura dayparting (horários ativos) na campanha. Cada schedule: {day_of_week, start_hour, end_hour, bid_modifier}. day_of_week: MONDAY..SUNDAY."""
    try:
        client = create_google_ads_client()
        resolver = ResourceResolver(client)

        res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
        if "error" in res_id: return res_id
        campaign_id_num = res_id["id"]

        campaign_service = client.get_service("CampaignService")
        campaign_criterion_service = client.get_service("CampaignCriterionService")
        campaign_rn = campaign_service.campaign_path(customer_id, campaign_id_num)

        ops = []
        for schedule in schedules:
            op = client.get_type("CampaignCriterionOperation")
            criterion = op.create
            criterion.campaign = campaign_rn
            criterion.ad_schedule.day_of_week = client.enums.DayOfWeekEnum[schedule["day_of_week"]]
            criterion.ad_schedule.start_hour = schedule["start_hour"]
            criterion.ad_schedule.end_hour = schedule["end_hour"]
            criterion.ad_schedule.start_minute = client.enums.MinuteOfHourEnum.ZERO
            criterion.ad_schedule.end_minute = client.enums.MinuteOfHourEnum.ZERO
            if "bid_modifier" in schedule:
                criterion.bid_modifier = schedule["bid_modifier"]
            ops.append(op)

        response = campaign_criterion_service.mutate_campaign_criteria(
            customer_id=str(customer_id), operations=ops
        )
        return {
            "status": "SUCCESS",
            "schedules_added": len(response.results),
            "campaign_id": campaign_id_num
        }
    except Exception as e:
        return translate_google_ads_error(e)


def search_geo_targets(location_name: str, country_code: str = "BR") -> dict:
    """[UTILITY] Busca IDs de localização por nome. Use antes de set_location_targeting."""
    try:
        client = create_google_ads_client()
        geo_target_service = client.get_service("GeoTargetConstantService")

        request = client.get_type("SuggestGeoTargetConstantsRequest")
        request.locale = "pt-BR"
        request.country_code = country_code
        request.names.extend([location_name])

        response = geo_target_service.suggest_geo_target_constants(request=request)
        results = []
        for suggestion in response.geo_target_constant_suggestions:
            geo = suggestion.geo_target_constant
            results.append({
                "id": geo.id,
                "name": geo.name,
                "country_code": geo.country_code,
                "target_type": geo.target_type,
                "resource_name": geo.resource_name
            })
        return {"status": "SUCCESS", "geo_targets": results}
    except Exception as e:
        return translate_google_ads_error(e)


def create_label(customer_id: str, name: str, description: str = "") -> dict:
    """[CREATE] Cria uma etiqueta para organizar campanhas, grupos e keywords."""
    try:
        client = create_google_ads_client()
        label_service = client.get_service("LabelService")

        op = client.get_type("LabelOperation")
        label = op.create
        label.name = name
        if description:
            label.description = description
        label.text_label.background_color = "#FFFFFF"

        response = label_service.mutate_labels(customer_id=str(customer_id), operations=[op])
        resource_name = response.results[0].resource_name
        label_id = resource_name.split("/")[-1]
        return {
            "status": "SUCCESS",
            "resource_name": resource_name,
            "label_id": label_id,
            "name": name
        }
    except Exception as e:
        return translate_google_ads_error(e)


def apply_label(customer_id: str, label_id: str, resource_type: str, resource_ids: list) -> dict:
    """[MUTATION] Aplica etiqueta a campanhas ou grupos. resource_type: CAMPAIGN|AD_GROUP|KEYWORD."""
    try:
        client = create_google_ads_client()
        label_rn = f"customers/{customer_id}/labels/{label_id}"

        if resource_type == "CAMPAIGN":
            service = client.get_service("CampaignLabelService")
            campaign_service = client.get_service("CampaignService")
            ops = []
            for res_id in resource_ids:
                op = client.get_type("CampaignLabelOperation")
                cl = op.create
                cl.campaign = campaign_service.campaign_path(customer_id, res_id)
                cl.label = label_rn
                ops.append(op)
            response = service.mutate_campaign_labels(customer_id=str(customer_id), operations=ops)
        elif resource_type == "AD_GROUP":
            service = client.get_service("AdGroupLabelService")
            ad_group_service = client.get_service("AdGroupService")
            ops = []
            for res_id in resource_ids:
                op = client.get_type("AdGroupLabelOperation")
                agl = op.create
                agl.ad_group = ad_group_service.ad_group_path(customer_id, res_id)
                agl.label = label_rn
                ops.append(op)
            response = service.mutate_ad_group_labels(customer_id=str(customer_id), operations=ops)
        else:
            return {"error": f"resource_type '{resource_type}' não suportado. Use CAMPAIGN ou AD_GROUP."}

        return {
            "status": "SUCCESS",
            "applied": len(response.results),
            "label_id": label_id,
            "resource_type": resource_type
        }
    except Exception as e:
        return translate_google_ads_error(e)


def list_labels(customer_id: str) -> dict:
    """[REPORT] Lista todas as etiquetas da conta e onde estão aplicadas."""
    try:
        client = create_google_ads_client()
        ga_service = client.get_service("GoogleAdsService")

        query = """
            SELECT
                label.id,
                label.name,
                label.status,
                label.resource_name
            FROM label
            WHERE label.status = 'ENABLED'
        """
        response = ga_service.search(customer_id=str(customer_id), query=query)
        results = [dense_proto_to_dict(row) for row in response]
        return {"status": "SUCCESS", "labels": results}
    except Exception as e:
        return translate_google_ads_error(e)


# ─────────────────────────────────────────────
# TIER 2 — ESTRATÉGIAS DE LANCE
# ─────────────────────────────────────────────

def list_bid_strategies(customer_id: str) -> dict:
    """[REPORT] Lista estratégias de lance de portfólio configuradas na conta."""
    try:
        client = create_google_ads_client()
        ga_service = client.get_service("GoogleAdsService")

        query = """
            SELECT
                bidding_strategy.id,
                bidding_strategy.name,
                bidding_strategy.type,
                bidding_strategy.status,
                bidding_strategy.campaign_count
            FROM bidding_strategy
            WHERE bidding_strategy.status = 'ENABLED'
        """
        response = ga_service.search(customer_id=str(customer_id), query=query)
        results = [dense_proto_to_dict(row) for row in response]
        return {"status": "SUCCESS", "bid_strategies": results}
    except Exception as e:
        return translate_google_ads_error(e)


def create_bid_strategy(customer_id: str, name: str, strategy_type: str, target_value: float = None) -> dict:
    """[CREATE] Cria estratégia de lance de portfólio. strategy_type: TARGET_CPA|TARGET_ROAS|MAXIMIZE_CONVERSIONS|MAXIMIZE_CONVERSION_VALUE."""
    try:
        client = create_google_ads_client()
        bidding_strategy_service = client.get_service("BiddingStrategyService")

        op = client.get_type("BiddingStrategyOperation")
        strategy = op.create
        strategy.name = name

        if strategy_type == "TARGET_CPA":
            client.copy_from(strategy.target_cpa, client.get_type("TargetCpa"))
            if target_value is not None:
                strategy.target_cpa.target_cpa_micros = int(target_value * 1e6)
        elif strategy_type == "TARGET_ROAS":
            client.copy_from(strategy.target_roas, client.get_type("TargetRoas"))
            if target_value is not None:
                strategy.target_roas.target_roas = target_value
        elif strategy_type == "MAXIMIZE_CONVERSIONS":
            client.copy_from(strategy.maximize_conversions, client.get_type("MaximizeConversions"))
        elif strategy_type == "MAXIMIZE_CONVERSION_VALUE":
            client.copy_from(strategy.maximize_conversion_value, client.get_type("MaximizeConversionValue"))
        else:
            return {"error": f"strategy_type '{strategy_type}' inválido. Use: TARGET_CPA, TARGET_ROAS, MAXIMIZE_CONVERSIONS, MAXIMIZE_CONVERSION_VALUE"}

        response = bidding_strategy_service.mutate_bidding_strategies(
            customer_id=str(customer_id), operations=[op]
        )
        resource_name = response.results[0].resource_name
        return {
            "status": "SUCCESS",
            "resource_name": resource_name,
            "strategy_id": resource_name.split("/")[-1],
            "name": name,
            "strategy_type": strategy_type
        }
    except Exception as e:
        return translate_google_ads_error(e)


def apply_bid_strategy(customer_id: str, campaign_id: str, bid_strategy_id: str) -> dict:
    """[MUTATION] Aplica uma estratégia de lance de portfólio a uma campanha."""
    try:
        client = create_google_ads_client()
        resolver = ResourceResolver(client)

        res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
        if "error" in res_id: return res_id
        campaign_id_num = res_id["id"]

        campaign_service = client.get_service("CampaignService")
        op = client.get_type("CampaignOperation")
        c = op.update
        c.resource_name = campaign_service.campaign_path(customer_id, campaign_id_num)
        c.bidding_strategy = f"customers/{customer_id}/biddingStrategies/{bid_strategy_id}"
        client.copy_from(op.update_mask, protobuf_helpers.field_mask(None, c._pb))

        campaign_service.mutate_campaigns(customer_id=str(customer_id), operations=[op])
        return {
            "status": "SUCCESS",
            "campaign_id": campaign_id_num,
            "bid_strategy_id": bid_strategy_id
        }
    except Exception as e:
        return translate_google_ads_error(e)


def create_conversion_action(customer_id: str, name: str, category: str, conversion_type: str = "WEBPAGE", default_value: float = 0.0) -> dict:
    """[CREATE] Cria uma nova ação de conversão. category: PURCHASE|LEAD|SIGNUP|PAGE_VIEW|OTHER."""
    try:
        client = create_google_ads_client()
        conversion_action_service = client.get_service("ConversionActionService")

        op = client.get_type("ConversionActionOperation")
        ca = op.create
        ca.name = name
        ca.category = client.enums.ConversionActionCategoryEnum[category]
        ca.type_ = client.enums.ConversionActionTypeEnum[conversion_type]
        ca.value_settings.default_value = default_value
        ca.counting_type = client.enums.ConversionActionCountingTypeEnum.ONE_PER_CLICK
        ca.status = client.enums.ConversionActionStatusEnum.ENABLED

        response = conversion_action_service.mutate_conversion_actions(
            customer_id=str(customer_id), operations=[op]
        )
        resource_name = response.results[0].resource_name
        return {
            "status": "SUCCESS",
            "resource_name": resource_name,
            "conversion_action_id": resource_name.split("/")[-1],
            "name": name,
            "category": category
        }
    except Exception as e:
        return translate_google_ads_error(e)


def upload_offline_conversions(customer_id: str, conversions: list) -> dict:
    """[MUTATION] Importa conversões offline (ex: vendas do CRM). Cada conversão: {gclid, conversion_action_id, conversion_date_time, conversion_value}."""
    try:
        client = create_google_ads_client()
        conversion_upload_service = client.get_service("ConversionUploadService")

        click_conversions = []
        for conv in conversions:
            click_conversion = client.get_type("ClickConversion")
            click_conversion.gclid = conv["gclid"]
            click_conversion.conversion_action = f"customers/{customer_id}/conversionActions/{conv['conversion_action_id']}"
            click_conversion.conversion_date_time = conv["conversion_date_time"]
            click_conversion.conversion_value = conv.get("conversion_value", 0.0)
            click_conversions.append(click_conversion)

        request = client.get_type("UploadClickConversionsRequest")
        request.customer_id = str(customer_id)
        request.conversions.extend(click_conversions)
        request.partial_failure = True

        response = conversion_upload_service.upload_click_conversions(request=request)
        return {
            "status": "SUCCESS",
            "uploaded": len(conversions),
            "partial_failure_error": str(response.partial_failure_error) if response.partial_failure_error else None
        }
    except Exception as e:
        return translate_google_ads_error(e)


def apply_recommendation(customer_id: str, recommendation_resource_name: str) -> dict:
    """[MUTATION] Aplica uma recomendação do Google Ads. Obtenha o resource_name via get_recommendations."""
    try:
        client = create_google_ads_client()
        recommendation_service = client.get_service("RecommendationService")

        op = client.get_type("ApplyRecommendationOperation")
        op.resource_name = recommendation_resource_name

        response = recommendation_service.apply_recommendations(
            customer_id=str(customer_id), operations=[op]
        )
        return {
            "status": "SUCCESS",
            "applied": len(response.results),
            "resource_name": recommendation_resource_name
        }
    except Exception as e:
        return translate_google_ads_error(e)


def dismiss_recommendation(customer_id: str, recommendation_resource_name: str) -> dict:
    """[MUTATION] Descarta uma recomendação do Google Ads."""
    try:
        client = create_google_ads_client()
        recommendation_service = client.get_service("RecommendationService")

        request = client.get_type("DismissRecommendationRequest")
        request.customer_id = str(customer_id)
        entry = client.get_type("DismissRecommendationRequest.DismissRecommendationEntry")
        entry.resource_name = recommendation_resource_name
        request.operations.append(entry)

        recommendation_service.dismiss_recommendations(request=request)
        return {
            "status": "SUCCESS",
            "dismissed": recommendation_resource_name
        }
    except Exception as e:
        return translate_google_ads_error(e)


def add_structured_snippet(customer_id: str, campaign_id: str, header: str, values: list) -> dict:
    """[MUTATION] Adiciona extensão de snippets estruturados. header: Serviços|Marcas|Cursos|etc. values: lista de até 10 itens."""
    try:
        client = create_google_ads_client()
        resolver = ResourceResolver(client)

        res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
        if "error" in res_id: return res_id
        campaign_id_num = res_id["id"]

        asset_service = client.get_service("AssetService")
        campaign_asset_service = client.get_service("CampaignAssetService")
        campaign_service = client.get_service("CampaignService")
        campaign_rn = campaign_service.campaign_path(customer_id, campaign_id_num)

        asset_op = client.get_type("AssetOperation")
        asset = asset_op.create
        asset.structured_snippet_asset.header = header
        asset.structured_snippet_asset.values.extend(values[:10])

        asset_res = asset_service.mutate_assets(customer_id=str(customer_id), operations=[asset_op])
        asset_rn = asset_res.results[0].resource_name

        ca_op = client.get_type("CampaignAssetOperation")
        ca = ca_op.create
        ca.asset = asset_rn
        ca.campaign = campaign_rn
        ca.field_type = client.enums.AssetFieldTypeEnum.STRUCTURED_SNIPPET
        campaign_asset_service.mutate_campaign_assets(customer_id=str(customer_id), operations=[ca_op])

        return {
            "status": "SUCCESS",
            "asset_id": asset_rn,
            "header": header,
            "values": values[:10],
            "campaign_id": campaign_id_num
        }
    except Exception as e:
        return translate_google_ads_error(e)


def add_promotion_extension(customer_id: str, campaign_id: str, promotion_text: str, discount_modifier: str, discount_value: float, final_url: str, start_date: str = None, end_date: str = None) -> dict:
    """[MUTATION] Adiciona extensão de promoção. discount_modifier: PERCENT_OFF|UP_TO_PERCENT_OFF|AMOUNT_OFF|UP_TO_AMOUNT_OFF."""
    try:
        client = create_google_ads_client()
        resolver = ResourceResolver(client)

        res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
        if "error" in res_id: return res_id
        campaign_id_num = res_id["id"]

        asset_service = client.get_service("AssetService")
        campaign_asset_service = client.get_service("CampaignAssetService")
        campaign_service = client.get_service("CampaignService")
        campaign_rn = campaign_service.campaign_path(customer_id, campaign_id_num)

        asset_op = client.get_type("AssetOperation")
        asset = asset_op.create
        asset.promotion_asset.promotion_text = promotion_text[:20]
        asset.promotion_asset.discount_modifier = client.enums.PromotionExtensionDiscountModifierEnum[discount_modifier]

        if "PERCENT" in discount_modifier:
            asset.promotion_asset.percent_off = int(discount_value * 100000)
        else:
            asset.promotion_asset.money_amount_off.amount_micros = int(discount_value * 1e6)
            asset.promotion_asset.money_amount_off.currency_code = "BRL"

        asset.promotion_asset.final_urls.append(final_url)

        if start_date:
            asset.promotion_asset.promotion_start_date = start_date
        if end_date:
            asset.promotion_asset.promotion_end_date = end_date

        asset_res = asset_service.mutate_assets(customer_id=str(customer_id), operations=[asset_op])
        asset_rn = asset_res.results[0].resource_name

        ca_op = client.get_type("CampaignAssetOperation")
        ca = ca_op.create
        ca.asset = asset_rn
        ca.campaign = campaign_rn
        ca.field_type = client.enums.AssetFieldTypeEnum.PROMOTION
        campaign_asset_service.mutate_campaign_assets(customer_id=str(customer_id), operations=[ca_op])

        return {
            "status": "SUCCESS",
            "asset_id": asset_rn,
            "promotion_text": promotion_text[:20],
            "campaign_id": campaign_id_num
        }
    except Exception as e:
        return translate_google_ads_error(e)


def create_shared_budget(customer_id: str, name: str, amount: float) -> dict:
    """[CREATE] Cria um orçamento compartilhado entre múltiplas campanhas."""
    try:
        client = create_google_ads_client()
        budget_service = client.get_service("CampaignBudgetService")

        op = client.get_type("CampaignBudgetOperation")
        budget = op.create
        budget.name = name
        budget.amount_micros = int(amount * 1e6)
        budget.explicitly_shared = True
        budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD

        response = budget_service.mutate_campaign_budgets(customer_id=str(customer_id), operations=[op])
        resource_name = response.results[0].resource_name
        return {
            "status": "SUCCESS",
            "resource_name": resource_name,
            "budget_id": resource_name.split("/")[-1],
            "name": name,
            "amount": amount
        }
    except Exception as e:
        return translate_google_ads_error(e)


def apply_shared_budget(customer_id: str, campaign_id: str, shared_budget_resource_name: str) -> dict:
    """[MUTATION] Aplica um orçamento compartilhado a uma campanha."""
    try:
        client = create_google_ads_client()
        resolver = ResourceResolver(client)

        res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
        if "error" in res_id: return res_id
        campaign_id_num = res_id["id"]

        campaign_service = client.get_service("CampaignService")
        op = client.get_type("CampaignOperation")
        c = op.update
        c.resource_name = campaign_service.campaign_path(customer_id, campaign_id_num)
        c.campaign_budget = shared_budget_resource_name
        client.copy_from(op.update_mask, protobuf_helpers.field_mask(None, c._pb))

        campaign_service.mutate_campaigns(customer_id=str(customer_id), operations=[op])
        return {
            "status": "SUCCESS",
            "campaign_id": campaign_id_num,
            "shared_budget": shared_budget_resource_name
        }
    except Exception as e:
        return translate_google_ads_error(e)


def link_shared_negative_list(customer_id: str, campaign_id: str, shared_set_id: str) -> dict:
    """[MUTATION] Aplica uma lista de negativos compartilhada a uma campanha."""
    try:
        client = create_google_ads_client()
        resolver = ResourceResolver(client)

        res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
        if "error" in res_id: return res_id
        campaign_id_num = res_id["id"]

        campaign_service = client.get_service("CampaignService")
        campaign_shared_set_service = client.get_service("CampaignSharedSetService")

        op = client.get_type("CampaignSharedSetOperation")
        css = op.create
        css.campaign = campaign_service.campaign_path(customer_id, campaign_id_num)
        css.shared_set = f"customers/{customer_id}/sharedSets/{shared_set_id}"

        response = campaign_shared_set_service.mutate_campaign_shared_sets(
            customer_id=str(customer_id), operations=[op]
        )
        return {
            "status": "SUCCESS",
            "resource_name": response.results[0].resource_name,
            "campaign_id": campaign_id_num,
            "shared_set_id": shared_set_id
        }
    except Exception as e:
        return translate_google_ads_error(e)


# ─────────────────────────────────────────────
# TIER 3 — DIFERENCIAL COMPETITIVO
# ─────────────────────────────────────────────

def get_reach_forecast(customer_id: str, keywords: list, daily_budget: float, date_range_days: int = 30) -> dict:
    """[RESEARCH] Estima alcance e frequência para um conjunto de keywords e orçamento."""
    return {
        "status": "SUCCESS",
        "note": "ReachPlanService requer configuração de produtos de mídia específicos. Use keyword_forecast para estimativas de volume de busca e cliques.",
        "suggestion": "Para previsões de Search, use keyword_forecast com a lista de keywords fornecida.",
        "keywords": keywords,
        "daily_budget": daily_budget
    }


def get_billing_info(customer_id: str) -> dict:
    """[UTILITY] Retorna informações de faturamento: método de pagamento, status e saldo."""
    try:
        client = create_google_ads_client()
        ga_service = client.get_service("GoogleAdsService")

        query = """
            SELECT
                billing_setup.id,
                billing_setup.status,
                billing_setup.start_date_time,
                billing_setup.payments_account
            FROM billing_setup
            WHERE billing_setup.status = 'APPROVED'
            LIMIT 1
        """
        response = ga_service.search(customer_id=str(customer_id), query=query)
        results = [dense_proto_to_dict(row) for row in response]
        return {"status": "SUCCESS", "billing_info": results[0] if results else None}
    except Exception as e:
        return translate_google_ads_error(e)


def list_invoices(customer_id: str, year: int = None, month: int = None) -> dict:
    """[UTILITY] Lista faturas da conta. Padrão: mês atual."""
    try:
        from datetime import datetime
        client = create_google_ads_client()
        ga_service = client.get_service("GoogleAdsService")
        invoice_service = client.get_service("InvoiceService")

        # Busca o billing_setup aprovado
        bs_query = "SELECT billing_setup.id, billing_setup.payments_account FROM billing_setup WHERE billing_setup.status = 'APPROVED' LIMIT 1"
        bs_response = ga_service.search(customer_id=str(customer_id), query=bs_query)
        bs_results = list(bs_response)
        if not bs_results:
            return {"status": "SUCCESS", "invoices": [], "note": "Nenhum billing_setup aprovado encontrado."}

        billing_setup_rn = f"customers/{customer_id}/billingSetups/{bs_results[0].billing_setup.id}"

        request = client.get_type("ListInvoicesRequest")
        request.customer_id = str(customer_id)
        request.billing_setup = billing_setup_rn
        request.issue_year = str(year or datetime.now().year)
        request.issue_month = client.enums.MonthOfYearEnum(month or datetime.now().month)

        response = invoice_service.list_invoices(request=request)
        invoices = []
        for inv in response.invoices:
            invoices.append({
                "id": inv.id,
                "total_amount_micros": inv.total_amount_micros,
                "corrected_total_amount_micros": inv.corrected_total_amount_micros,
                "due_date": inv.due_date,
                "issue_date": inv.issue_date,
                "service_date_range_start": inv.service_date_range.start_date,
                "service_date_range_end": inv.service_date_range.end_date
            })
        return {"status": "SUCCESS", "invoices": invoices}
    except Exception as e:
        return translate_google_ads_error(e)


def upload_customer_match(customer_id: str, list_name: str, emails: list, membership_life_span: int = 30) -> dict:
    """[CREATE] Cria audiência Customer Match a partir de lista de emails para remarketing."""
    import hashlib
    try:
        client = create_google_ads_client()
        user_list_service = client.get_service("UserListService")

        # Passo 1: Cria UserList
        ul_op = client.get_type("UserListOperation")
        user_list = ul_op.create
        user_list.name = list_name
        user_list.crm_based_user_list.upload_key_type = client.enums.CustomerMatchUploadKeyTypeEnum.CONTACT_INFO
        user_list.membership_life_span = membership_life_span

        ul_response = user_list_service.mutate_user_lists(customer_id=str(customer_id), operations=[ul_op])
        user_list_rn = ul_response.results[0].resource_name

        # Passo 2: Cria OfflineUserDataJob
        offline_job_service = client.get_service("OfflineUserDataJobService")

        job_op = client.get_type("OfflineUserDataJob")
        job_op.type_ = client.enums.OfflineUserDataJobTypeEnum.CUSTOMER_MATCH_USER_LIST
        job_op.customer_match_user_list_metadata.user_list = user_list_rn

        job_response = offline_job_service.create_offline_user_data_job(
            customer_id=str(customer_id), job=job_op
        )
        job_rn = job_response.resource_name

        # Passo 3: Adiciona emails com hash SHA256
        user_data_list = []
        for email in emails:
            hashed_email = hashlib.sha256(email.lower().strip().encode()).hexdigest()
            user_data = client.get_type("UserData")
            identifier = client.get_type("UserIdentifier")
            identifier.hashed_email = hashed_email
            user_data.user_identifiers.append(identifier)
            user_data_list.append(user_data)

        add_request = client.get_type("AddOfflineUserDataJobOperationsRequest")
        add_request.resource_name = job_rn
        for ud in user_data_list:
            op = client.get_type("OfflineUserDataJobOperation")
            client.copy_from(op.create, ud)
            add_request.operations.append(op)

        offline_job_service.add_offline_user_data_job_operations(request=add_request)

        # Passo 4: Executa o job
        offline_job_service.run_offline_user_data_job(resource_name=job_rn)

        return {
            "status": "SUCCESS",
            "job_resource_name": job_rn,
            "user_list_resource_name": user_list_rn,
            "emails_uploaded": len(emails),
            "note": "Job em processamento assíncrono. Pode levar alguns minutos para a lista ser populada."
        }
    except Exception as e:
        return translate_google_ads_error(e)


def create_audience(customer_id: str, name: str, description: str = "", dimensions: list = None) -> dict:
    """[CREATE] Cria audiência personalizada combinando sinais (interesses, URLs visitadas, apps)."""
    try:
        client = create_google_ads_client()
        audience_service = client.get_service("AudienceService")

        op = client.get_type("AudienceOperation")
        audience = op.create
        audience.name = name
        if description:
            audience.description = description
        audience.status = client.enums.AudienceStatusEnum.ENABLED

        if dimensions:
            for dim in dimensions:
                dimension = client.get_type("AudienceDimension")
                if dim.get("type") == "INTEREST" and dim.get("interest_category_constant"):
                    dimension.audience_segments.segments.append(
                        client.get_type("AudienceSegment")
                    )
                audience.dimensions.append(dimension)

        response = audience_service.mutate_audiences(customer_id=str(customer_id), operations=[op])
        resource_name = response.results[0].resource_name
        return {
            "status": "SUCCESS",
            "resource_name": resource_name,
            "audience_id": resource_name.split("/")[-1],
            "name": name
        }
    except Exception as e:
        return translate_google_ads_error(e)


def set_campaign_targeting_setting(customer_id: str, campaign_id: str, targeting_dimension: str, bid_only: bool = True) -> dict:
    """[MUTATION] Configura se um targeting dimension é para observação (bid_only=True) ou segmentação (bid_only=False). targeting_dimension: AUDIENCE|PLACEMENT|TOPIC."""
    try:
        client = create_google_ads_client()
        resolver = ResourceResolver(client)

        res_id = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
        if "error" in res_id: return res_id
        campaign_id_num = res_id["id"]

        campaign_service = client.get_service("CampaignService")
        op = client.get_type("CampaignOperation")
        c = op.update
        c.resource_name = campaign_service.campaign_path(customer_id, campaign_id_num)

        target_restriction = client.get_type("TargetRestriction")
        target_restriction.targeting_dimension = client.enums.TargetingDimensionEnum[targeting_dimension]
        target_restriction.bid_only = bid_only
        c.targeting_setting.target_restrictions.append(target_restriction)

        client.copy_from(op.update_mask, protobuf_helpers.field_mask(None, c._pb))
        campaign_service.mutate_campaigns(customer_id=str(customer_id), operations=[op])

        return {
            "status": "SUCCESS",
            "campaign_id": campaign_id_num,
            "targeting_dimension": targeting_dimension,
            "bid_only": bid_only,
            "mode": "OBSERVATION" if bid_only else "TARGETING"
        }
    except Exception as e:
        return translate_google_ads_error(e)


def get_network_performance(customer_id: str, date_range: str = "LAST_30_DAYS", campaign_id: str = None) -> dict:
    """[REPORT] Performance por rede de distribuição: Google Search, Search Partners, Display Network."""
    try:
        client = create_google_ads_client()
        ga_service = client.get_service("GoogleAdsService")

        campaign_filter = ""
        if campaign_id:
            resolver = ResourceResolver(client)
            res = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
            if "error" in res:
                return res
            campaign_filter = f"AND campaign.id = {res['id']}"

        query = f"""
            SELECT
                segments.ad_network_type,
                campaign.id, campaign.name,
                metrics.clicks, metrics.impressions, metrics.cost_micros,
                metrics.conversions, metrics.ctr, metrics.average_cpc
            FROM campaign
            WHERE segments.date DURING {date_range}
            AND campaign.status != 'REMOVED'
            {campaign_filter}
            ORDER BY metrics.cost_micros DESC
        """
        rows = ga_service.search(customer_id=str(customer_id), query=query)
        results = [dense_proto_to_dict(row) for row in rows]
        return {"status": "SUCCESS", "date_range": date_range, "network_performance": results}
    except Exception as e:
        return translate_google_ads_error(e)


def set_ad_group_bid(customer_id: str, ad_group_id: str, cpc_bid: float) -> dict:
    """[MUTATION] Atualiza o CPC padrão de um grupo de anúncios. Aceita ID numérico ou Nome do Ad Group."""
    try:
        client = create_google_ads_client()
        resolver = ResourceResolver(client)

        res = resolver.resolve(customer_id, "AD_GROUP", ad_group_id)
        if "error" in res:
            return res
        ad_group_id_num = res["id"]

        service = client.get_service("AdGroupService")
        op = client.get_type("AdGroupOperation")
        ag = op.update
        ag.resource_name = service.ad_group_path(customer_id, ad_group_id_num)
        ag.cpc_bid_micros = int(cpc_bid * 1_000_000)
        client.copy_from(op.update_mask, protobuf_helpers.field_mask(None, ag._pb))

        service.mutate_ad_groups(customer_id=str(customer_id), operations=[op])
        return {"status": "SUCCESS", "ad_group_id": ad_group_id_num, "new_cpc_bid": cpc_bid}
    except Exception as e:
        return translate_google_ads_error(e)


def create_shared_negative_list(customer_id: str, name: str, keywords: list = None, match_type: str = "BROAD") -> dict:
    """[CREATE] Cria lista de palavras-chave negativas compartilhada. Opcionalmente já adiciona keywords na lista."""
    try:
        client = create_google_ads_client()

        # Passo 1: Criar SharedSet
        shared_set_service = client.get_service("SharedSetService")
        ss_op = client.get_type("SharedSetOperation")
        shared_set = ss_op.create
        shared_set.name = name
        shared_set.type_ = client.enums.SharedSetTypeEnum.NEGATIVE_KEYWORDS

        ss_res = shared_set_service.mutate_shared_sets(customer_id=str(customer_id), operations=[ss_op])
        shared_set_rn = ss_res.results[0].resource_name
        shared_set_id = shared_set_rn.split("/")[-1]

        # Passo 2: Adicionar keywords se fornecidas
        keywords_added = 0
        if keywords:
            sc_service = client.get_service("SharedCriterionService")
            sc_ops = []
            for kw in keywords:
                sc_op = client.get_type("SharedCriterionOperation")
                sc = sc_op.create
                sc.shared_set = shared_set_rn
                sc.keyword.text = kw
                sc.keyword.match_type = client.enums.KeywordMatchTypeEnum[match_type]
                sc_ops.append(sc_op)
            sc_service.mutate_shared_criteria(customer_id=str(customer_id), operations=sc_ops)
            keywords_added = len(keywords)

        return {
            "status": "SUCCESS",
            "shared_set_id": shared_set_id,
            "resource_name": shared_set_rn,
            "keywords_added": keywords_added
        }
    except Exception as e:
        return translate_google_ads_error(e)


def remove_campaign_asset(customer_id: str, campaign_asset_resource_name: str) -> dict:
    """[MUTATION] Remove uma extensão/asset de uma campanha. Obtenha o resource_name via search_ads ou list dos assets da campanha."""
    try:
        client = create_google_ads_client()
        service = client.get_service("CampaignAssetService")

        op = client.get_type("CampaignAssetOperation")
        op.remove = campaign_asset_resource_name

        service.mutate_campaign_assets(customer_id=str(customer_id), operations=[op])
        return {"status": "SUCCESS", "removed": campaign_asset_resource_name}
    except Exception as e:
        return translate_google_ads_error(e)


def add_price_extension(customer_id: str, campaign_id: str, price_qualifier: str, language_code: str, items: list) -> dict:
    """
    [MUTATION] Adiciona extensão de tabela de preços a uma campanha.
    price_qualifier: NONE|FROM|UP_TO|AVERAGE.
    Cada item: {header, description, price, currency_code, unit, final_url}.
    unit: PER_HOUR|PER_DAY|PER_WEEK|PER_MONTH|PER_YEAR|PER_NIGHT|PER_UNIT|UNSPECIFIED.
    """
    try:
        client = create_google_ads_client()
        resolver = ResourceResolver(client)

        res = resolver.resolve(customer_id, "CAMPAIGN", campaign_id)
        if "error" in res:
            return res
        campaign_id_num = res["id"]

        # Criar Asset de Preço
        asset_service = client.get_service("AssetService")
        asset_op = client.get_type("AssetOperation")
        asset = asset_op.create

        asset.price_asset.type_ = client.enums.PriceExtensionTypeEnum.SERVICES
        asset.price_asset.price_qualifier = client.enums.PriceExtensionPriceQualifierEnum[price_qualifier]
        asset.price_asset.language_code = language_code

        items_to_add = items[:8]
        for item in items_to_add:
            offering = client.get_type("PriceOffer")
            offering.header = item["header"][:25]
            offering.description = item["description"][:25]
            offering.price.amount_micros = int(item["price"] * 1_000_000)
            offering.price.currency_code = item.get("currency_code", "BRL")
            offering.unit = client.enums.PriceExtensionPriceUnitEnum[item.get("unit", "UNSPECIFIED")]
            offering.final_urls.append(item["final_url"])
            asset.price_asset.price_offerings.append(offering)

        asset_res = asset_service.mutate_assets(customer_id=str(customer_id), operations=[asset_op])
        asset_rn = asset_res.results[0].resource_name

        # Vincular à Campanha
        campaign_service = client.get_service("CampaignService")
        ca_service = client.get_service("CampaignAssetService")
        ca_op = client.get_type("CampaignAssetOperation")
        ca = ca_op.create
        ca.asset = asset_rn
        ca.campaign = campaign_service.campaign_path(customer_id, campaign_id_num)
        ca.field_type = client.enums.AssetFieldTypeEnum.PRICE

        ca_service.mutate_campaign_assets(customer_id=str(customer_id), operations=[ca_op])

        return {
            "status": "SUCCESS",
            "asset_id": asset_rn,
            "items_added": len(items_to_add),
            "campaign_id": campaign_id_num
        }
    except Exception as e:
        return translate_google_ads_error(e)


if __name__ == "__main__":
    mcp.run()

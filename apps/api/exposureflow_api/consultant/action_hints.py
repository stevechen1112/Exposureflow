"""Plain-language consultant instructions for inbox items."""

from __future__ import annotations

_GSC_ISSUE_HINTS = {
    "gsc_sitemap_unreachable": (
        "到「技術問題」查看 live 診斷；修正 sitemap 或站點 base URL（常見為 localhost／錯誤網域），"
        "儲存後至「整合設定」手動觸發 GSC 同步，並等待排程重檢。"
    ),
    "gsc_sitemap_missing": (
        "到「整合設定」確認 GSC 已連線，並在 Google Search Console 提交正確的 sitemap.xml；"
        "回到「技術問題」確認是否已消除。"
    ),
    "gsc_sitemap_api_error": (
        "到「整合設定」檢查 GSC 憑證是否過期，重新授權後手動同步；若仍失敗請記錄錯誤並聯繫平台支援。"
    ),
}


def hint_for_technical(issue_type: str, recommended_action: str | None, evidence_summary: str | None) -> str:
    base = _GSC_ISSUE_HINTS.get(issue_type)
    if base:
        return base
    if evidence_summary:
        return f"{evidence_summary}。請到「技術問題」依建議處置並標記已處理。"
    if recommended_action:
        return f"{recommended_action}。請到「技術問題」完成修復後等待重檢。"
    return "到「技術問題」查看細節，完成修復後等待自動重檢或手動觸發相關同步。"


def hint_for_decision(action_type: str) -> str:
    return (
        f"到「機會佇列」檢視「{action_type}」建議；核准後系統才會執行，拒絕則從待辦移除。"
    )


def hint_for_content(status: str) -> str:
    hints = {
        "needs_review": "到「內容審核」通讀全文，確認事實與 Claims 無誤後核准發布，或退回要求修改。",
        "needs_changes": "到「內容審核」依審核意見修改文章，修改完成後重新送審。",
        "claim_verified": "Claims 已通過驗證；到「內容審核」做最後核准並發布上線。",
        "claim_blocked": "Claims 未通過；到「內容審核」修改內容或補強知識庫後，重新跑驗證流程。",
        "draft": "草稿尚未進審核；到「內容審核」啟動審核流程，或安排撰寫完成後再送審。",
    }
    return hints.get(status, "到「內容審核」處理此內容項目。")


def hint_for_keyword_pyramid(keyword: str, node_type: str) -> str:
    return (
        f"到「關鍵字金字塔」確認「{keyword}」（{node_type}）是否符合案型與商業範圍；"
        "核准後才會進入內容排程，不符則標為排除。"
    )


def hint_for_topic_gap(keyword: str, impressions: int) -> str:
    imp = f"近況約 {impressions:,} 次曝光" if impressions else "有搜尋需求"
    return (
        f"GSC 顯示「{keyword}」{imp}，但站內尚無對應內容。"
        "到「曝光地圖」檢視所屬 Topic Cluster，排入內容 brief 或與客戶確認是否不需覆蓋。"
    )


def hint_for_indexability(rule_id: str, evidence_summary: str | None) -> str:
    prefix = evidence_summary or f"索引問題（{rule_id or '修復項目'}）"
    return f"{prefix}。到「機會佇列」執行修復建議，或到「技術問題」處理根本原因。"


def hint_for_sync(provider: str) -> str:
    return (
        f"「{provider}」同步失敗；到「整合設定」檢查憑證與連線，修復後手動觸發同步並確認錯誤已清除。"
    )


def hint_for_roadmap(title: str, status: str, week_number: int | None) -> str:
    week = f"第 {week_number} 週" if week_number else "本階段"
    if status == "planned":
        return f"路線圖「{title}」為{week}計畫；到「路線圖」確認是否本週啟動或調整排程。"
    return f"路線圖「{title}」進行中（{week}）；到「路線圖」更新進度或標記完成。"


def hint_for_open_opportunity(label: str) -> str:
    return (
        f"曝光機會「{label}」尚待評估；到「機會佇列」決定是否立案內容、技術修復或暫緩。"
    )

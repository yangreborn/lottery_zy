DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def parse_page_params(query_params):
    """从 query 解析 (page, page_size)，非法值回落到默认，page_size 上限 100。"""
    try:
        page = int(query_params.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(query_params.get("page_size", DEFAULT_PAGE_SIZE))
    except (TypeError, ValueError):
        page_size = DEFAULT_PAGE_SIZE
    page = max(page, 1)
    page_size = max(1, min(page_size, MAX_PAGE_SIZE))
    return page, page_size


def paginate(qs, page, page_size):
    """返回 (当前页 queryset 切片, total)。"""
    total = qs.count()
    start = (page - 1) * page_size
    return qs[start:start + page_size], total

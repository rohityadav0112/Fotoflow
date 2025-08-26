def search_query(request):
    return {"query": request.GET.get("q", "")}
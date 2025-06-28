from vdbpy.config import WEBSITE
from vdbpy.utils.network import fetch_json


def get_tag_by_id(tag_id, fields=""):
    params = {"fields": fields} if fields else {}
    url = f"{WEBSITE}/api/tags/{tag_id}"
    """
    categoryName	"Themes"
    createDate	"2019-11-30T03:14:48.553"
    defaultNameLanguage	"English"
    id	7339
    name	"literature"
    status	"Finished"
    targets	1073741823
    newTargets
        0	"all"
    urlSlug	"literature"
    usageCount	369
    version	7
    """
    return fetch_json(url, params=params)

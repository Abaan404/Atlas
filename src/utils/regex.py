import re


def regex_channel(text): return re.search("^<#(\d+)>$", text)
def regex_user(text): return re.search("^<@(\d+)>$", text)
def regex_snowflake(text): return re.search("^<*(\d+)>$", text)
# def regex_url(text): return re.search(f"^(http|https):\/\/", text)
def regex_url(text, domain, sub="www", top="com"): return re.search(f"^(http|https):\/\/({sub}.|){domain}.{top}\/", text)
def regex_time_24h(text): return re.search("^(2[0-3]|1[0-9]|0[0-9]):(0[0-9]|[1-5][0-9])$", text)

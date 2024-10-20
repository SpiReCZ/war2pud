
def append_sitemap(file, json_file, preview_file, sitemap):
    sitemap.append({
        "file": file,
        "metadata": json_file,
        "picture": preview_file,
    })
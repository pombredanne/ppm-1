function (doc) {
    urls = [];
    if (doc.versions) {
        for (v in doc.versions) {
            if (doc.versions[v].url) {
                urls.push(doc.versions[v].url);
            }
        }
    }
    if (urls.length > 0) {
        emit(doc._id, urls);
    }
};
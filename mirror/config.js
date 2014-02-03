var path = require("path");

var config = {
	// host adress and port to run mirror server on
	MIRROR_SERVER_HOST: "127.0.0.1",
	MIRROR_SERVER_PORT: 8888,

	// link to registry list of urls to mirror
	REGISTRY_SERVER_URLSLIST_URL: "http://127.0.0.1:5984/packages/_design/main/_view/urlslist",
	// how often check registry for updates
	CHECK_INTERVALL: 3600 * 1000, //every hour

	// parser of REGISTRY_SERVER_URLS_ABSOLUTE_PATH response returning a list of urls
	// change this according to your registry sever response details
	parse_remote_urllist: function(respBody) {
		var data = JSON.parse(respBody);
		if (! data.rows)
			return [];
		urls = [];
		for (var i =0; i < data.rows.length; i++) {
			urls = urls.concat(data.rows[i].value);
		}
		return urls;
	},

	// directory where to download packages
	PACKAGES_DIRECTORY_PATH: path.join(process.cwd(), "packages"),
	// file where to store a map between origin urls and local filenames
	MAPFILE_NAME: "urlmap.json"
};

if (typeof module !== 'undefined' && module.exports) {
        module.exports = config;
}

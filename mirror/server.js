var http = require("http"),
    url = require("url"),
    path = require("path"),
    fs = require("fs");

var host = process.argv[2] || '127.0.0.1';
var port = process.argv[3] || 8888;

var PACKAGES_FOLDER_NAME = "packages"
var MAP_FILE = "urlmap.json";

var extTypes = {
    "gz": "application/x-gzip",
    "js": "application/javascript",
    "json": "application/json",
    "tar": "application/x-tar",
    "zip": "application/zip",
    "bz2": "application/x-bzip2"
}

http.createServer(function (request, response) {
    if (request.method == 'POST') {
        // handling post requests for checking if a remote url is present in the mirror server
        var requestedPackage = '';
        request.on('data', function (data) {
            requestedPackage += data;
        });
        request.on('end', function () {
            console.log("Requesting "+requestedPackage);
            var mapfile = path.join(PACKAGES_FOLDER_NAME, MAP_FILE);
            // reading the mapfile for every POST request because it might be updated
            if (fs.existsSync(mapfile)){
                var fbody = JSON.parse(fs.readFileSync(mapfile));
                if (fbody.hasOwnProperty(requestedPackage)){
                    response.writeHead(200, {'Content-Type': 'text/html'});
                    response.end("http://"+host+":"+port+"/"+fbody[requestedPackage]+"\n");
                    return;
                }
            }
            response.writeHead(404, {'Content-Type': 'text/html'});
            response.write("404 url does not exist\n");
            response.end();
        });

    } else {
        // static file server
        var uri = url.parse(request.url).pathname
        var filepath = path.join(process.cwd(), PACKAGES_FOLDER_NAME, uri);

        path.exists(filepath, function (exists) {
            if (!exists) {
                response.writeHead(404, {
                    "Content-Type": "text/plain"
                });
                response.write("404 Not Found\n");
                response.end();
                return;
            }

            if (fs.statSync(filepath).isDirectory()) {
                response.writeHead(403, {
                    "Content-Type": "text/plain"
                });
                response.write("Access Forbidden\n");
                response.end();
                return;
            }

            fs.readFile(filepath, "binary", function (err, file) {
                if (err) {
                    response.writeHead(500, {
                        "Content-Type": "text/plain"
                    });
                    response.write(err + "\n");
                    response.end();
                    return;
                }
                var ext = path.extname(filepath).replace(".","")
                response.writeHead(200, {
                    'Content-Type': getContentType(ext),
                    'Content-disposition': 'attachment; filename=' + path.basename(filepath)
                });
                response.write(file, "binary");
                response.end();
            });
        });
    }
}).listen(parseInt(port, 10), host);

var getContentType = function (ext) {
    return extTypes[ext.toLowerCase()] || 'application/octet-stream';
}

console.log("Mirror file server running at http://"+host+":" + port + "");

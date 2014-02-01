var http = require("http"),
    url = require("url"),
    path = require("path"),
    fs = require("fs");

var run = function(adress, port, packages_dir_path, map_file) {
    http.createServer(function (request, response) {
        if (request.method == 'POST') {
            // handling post requests for checking if a remote url is present in the mirror server
            var requestedPackage = '';
            request.on('data', function (data) {
                requestedPackage += data;
            });
            request.on('end', function () {
                console.log("Requesting "+requestedPackage);
                // reading the map_file for every POST request because it might be updated
                if (fs.existsSync(map_file)){
                    var fbody = JSON.parse(fs.readFileSync(map_file));
                    if (fbody.hasOwnProperty(requestedPackage)){
                        response.writeHead(200, {'Content-Type': 'text/html'});
                        response.end("http://"+adress+":"+port+"/"+fbody[requestedPackage]+"\n");
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
            var filepath = path.join(packages_dir_path, uri);

            fs.exists(filepath, function (exists) {
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
                
                response.setHeader('Content-disposition', 'attachment; filename='+path.basename(filepath));
                var ext = path.extname(filepath).substr(".".length);
                response.setHeader('Content-type', getContentType(ext));
                
                var file = fs.createReadStream(filepath);
                file.pipe(response);

                file.on("error", function(err) {
                    response.writeHead(500, {
                            "Content-Type": "text/plain"
                        });
                    response.write(err + "\n");
                    response.end();
                    console.log("Error piping from file to client: "+err)
                });
            });
        }
        request.on('error', function(err) {console.log("Error handling request: "+err)});
        response.on('error', function(err) {console.log("Error handling request: "+err)});
    }).listen(parseInt(port, 10), adress);
    console.log("Mirror file server running at http://"+adress+":" + port + "");
};

var extTypes = {
    "gz": "application/x-gzip",
    "js": "application/javascript",
    "json": "application/json",
    "tar": "application/x-tar",
    "zip": "application/zip",
    "bz2": "application/x-bzip2"
};
var getContentType = function (ext) {
    return extTypes[ext.toLowerCase()] || 'application/octet-stream';
};

if (typeof module !== 'undefined' && module.exports) {
        module.exports = {'run': run};
}
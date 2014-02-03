var request = require('request'),
    url = require("url"),
    path = require("path"),
    fs = require("fs");

// check registry for new packages and download them locally
var check_registry_updates = function(registry_urls_url, download_dir, map_file, parse_res) {
    console.log("checking for registry update");
    var request = require('request');
    request(registry_urls_url, function (error, response, body) {
        if (!error && response.statusCode == 200) {
            process_urls(parse_res(body), download_dir, map_file);
        }
        else {
            console.log("error downloading registry urls: "+ (error || response.statusCode));
        }
    });
};

// compare urls against local map file, and download new packages
var process_urls = function (urls, download_dir, map_file) {
    // set urls being downloaded into a being_processed property
    if (!process_urls.being_processed) {
        process_urls.being_processed = [];
    }
    var map = {};
    if (fs.existsSync(map_file)){
    	map = JSON.parse(fs.readFileSync(map_file, 'utf8'));
    }

    for (var i = 0; i < urls.length; i++) {
        !function (i){
            var url = urls[i];
            if (! map[url] && process_urls.being_processed.indexOf(url) == -1) {
                console.log("new package: "+ url);
                process_urls.being_processed.push(url); 
                download(url, download_dir, function (filename) {
                    map[url] = filename;
                    fs.writeFileSync(map_file, JSON.stringify(map));
                    console.log("package saved to "+filename);
                    process_urls.being_processed.splice(process_urls.being_processed.indexOf(url),1);
                }, function (err){
                    console.log("Error downloading "+url+": "+err);
                    process_urls.being_processed.splice(process_urls.being_processed.indexOf(url),1);
                });
            }
        }(i);
    }
};

var download = function (url, download_dir, cb, errcb) {
    var req = request(url);
    req.on('response', function (res) {
        var filename;
        if (res.headers["Content-Disposition"])
            filename = res.headers["Content-Disposition"];
        else
            filename = path.basename(url);
        var savePath = path.join(download_dir, filename);
        //TODO: check for file extension
        //TODO : check for file existence
        var fileStream = fs.createWriteStream(savePath);
        res.pipe(fileStream);
        fileStream.on('finish', function () {
            fileStream.close();
            if (cb)
                cb(filename);
        });
        fileStream.on('error', function(err){
            if (errcb)
                errcb(err);
        });
        res.on('error', function(err){
            if (errcb)
                errcb(err);
        });

    });
    req.on('error',function (err){
        if (errcb)
            errcb(err);
    });
};

if (typeof module !== 'undefined' && module.exports) {
        module.exports.check_registry_updates = check_registry_updates;
}
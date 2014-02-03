var config = require("./config"),
    repositoryServer = require("./server"),
    monitor = require("./monitor"),
    path = require("path"),
    fs = require("fs");

// TODO: assert that the path refer to a directory (not a file)
if (! fs.existsSync(config.PACKAGES_DIRECTORY_PATH)){
    fs.mkdirSync(config.PACKAGES_DIRECTORY_PATH);
}
var map_file = path.join(config.PACKAGES_DIRECTORY_PATH, config.MAPFILE_NAME);
// run repository server
repositoryServer.run(config.REPOSITORY_SERVER_HOST, config.REPOSITORY_SERVER_PORT, config.PACKAGES_DIRECTORY_PATH, map_file);
// check registry for new packages every x seconds
setInterval(function (){
    monitor.check_registry_updates(config.REGISTRY_SERVER_URLSLIST_URL,
        config.PACKAGES_DIRECTORY_PATH,
        map_file,
        config.parse_remote_urllist
        );
}, config.CHECK_INTERVALL);
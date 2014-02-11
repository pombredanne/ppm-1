ppm
===

Project Package Manager

This is not a replacement of language/platform dependent package managers (like Python pip or node.js npm), it's destined for managing general project dependencies, especially binaries, and setting a "virtual-like" environment.

currently, there is no standard repository which holds packages, it's the role of a project member to create a packages registry and add meta information of required binaries (creating Packages).

PPM offers also the possiblity of using a repository server (which contains binaries), useful in case you want to download archives and serve them from that repository.

## Quick Start

download and install ppm using:  
`sudo pip install ppm`  

set registry server:  
`pip set registry-server http://your-registry-url:port`

set repository server(optional):  
`pip set repository-server http://your-repository-url:port`


### synchronizing dependencies
`sync` is the main ppm command, it is used to synchronize your current dependencies with required project dependencies,
required project dependencies can be specified either locally in a `ppmdependencies.json` file, or in the registry server(you can set current project using `ppm set project sampleproject`).   
  
To run the synchronization operation type:  
`ppm sync`

### downloading dependencies
PPM offers the possibility of downloading tarballs without installing them, using the command `ppm download`.  
Some examples (type `ppm download -h` for more details):  
`ppm download python@2.7.1 --directory pythondep`  # download python version 2.7.1 to pythondep directory  
`ppm download nodejs@latest python@2.7.1` # download nodejs latest version and python 2.7.1 to current directory

## Registry server Configuration:
the easiest way to setup a registry server is to use the existing config in the registry directory and load it to a couchdb database using couchapp.

### creating a package:
a package have the following JSON structure:
```JSON
{
   "_id": "nodejs",
   "description": "Node.js is a platform built on Chrome's JavaScript runtime for easily building fast, scalable network applications",
   "directoryname": "node",
   "env": [
       "export NODEJS_HOME=\"${HOME}\"",
       "export PATH=\"${NODEJS_HOME}:$PATH\""
   ],
   "versions": {
       "0.10.25": {
           "url": "http://nodejs.org/dist/v0.10.25/node-v0.10.25.tar.gz"
       },
       "0.10.10": {
       	   "url": "http://nodejs.org/dist/v0.10.10/node-v0.10.10.tar.gz"
	   }
   }
}
```
####notes:

`_id` the identifier of package (requesting packages/package._id returns the above json data). 

`env` is a bash script that ppm use to construct the environment shell script (${HOME} refer to the home directory of package).


### creating a project:
a project have the following JSON structure:
```JSON
{
   "_id": "ppmdemo",
   "description": "a ppm demo",
   "devdependencies": {
       "nodejs": "0.10.25",
       "phantomjs": "1.9.6",
   }
}
```

## Repository server configuration
clone the repository directory, open `config.js` and configure it to match your needs. Than type in the command line:  
```
npm install
node main.js
```

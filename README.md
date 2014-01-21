ppm
===

Project Package Manager

this is not a replacement of language/platform dependent package managers (like Python pip or node.js npm), it's destined for managing
unspecific project dependencies, especially binaries. 

because it's not targeted for specific platform or language, there is no repository which holds dependencies, it's the role of a project member to create a dependencies-info file which contains information about project dependencies (url, install location...), this is why it's called Project Package Manager.

the principal goal of the tool is to ensure that all project members possess the same tools (eliminate works on my machine!), and they can install, update and remove dependencies easily.
another advantage of ppm is that you can easily mirror dependencies-info file locally,
this is useful to cache dependencies in a local server, and serve dependencies locally to save bandwidth (useful for large dependencies)

this tool is usually used with a shell script that override PATH environment variable to local dependencies locations.

## How it works

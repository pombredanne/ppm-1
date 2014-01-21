ppm
===

Project Package Manager

This is not a replacement of language/platform dependent package managers (like Python pip or node.js npm), it's destined for managing general project dependencies, especially binaries. 

Because it's not targeted for a specific platform or a language, there is no repository which holds dependencies, it's the role of a project member to create a dependencies-info file which contains information about the project dependencies (url, install location...), this is why it's called Project Package Manager.

The main goal of the tool is to ensure that all project members possess the same tools (eliminate works on my machine!), and can install, update and remove dependencies easily.
Another advantage of ppm is that it makes it easier to mirror the dependencies-info file locally.
This is useful to cache dependencies in a local server, and serve the dependencies locally to save bandwidth (useful for large dependencies).

This tool is usually used with a shell script that overrides the PATH environment variable to the local dependencies locations.

## How it works

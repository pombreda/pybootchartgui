# pybootchartgui has been replaced by [bootchart2](https://github.com/mmeeks/bootchart) #

Active development of the bootchart logger and the python gui continues on github as [bootchart2](https://github.com/mmeeks/bootchart) with Michael Meeks and Riccardo Magliocchetti as the main developers


## About pybootchart gui ##

pybootchartgui is a tool for visualization and analysis of the
GNU/Linux boot process. It renders the output of the boot-logger tool
[bootchart](http://www.bootchart.org) interactively or to files of
various formats. Bootchart collects information about the processes,
their dependencies, and resource consumption during boot of a
GNU/Linux system. The pybootchartgui tools visualizes the process tree
and overall resource utilization.

pybootchartgui is a port of the visualization part of bootchart from
Java to Python and Cairo.

## Status ##

We have reached our first milestone! pybootchartgui matches the
features of the visualization part of bootchart. It is possible to
render bootcharts interactively as well as to files, and the rendered
charts are very similar to the charts produced by the original tool.

pybootchartgui is available in the latest release of Ubuntu and as a tarball [here](http://pybootchartgui.googlecode.com/files/pybootchartgui-r124.tar.gz).

The plan is to extend pybootchartgui to be more usable and we are
currently looking into in which directions to take the program and
which future milestones to work towards. Comments, bugreports and
feature requests are most welcome!

![http://pybootchartgui.googlecode.com/svn/trunk/examples/1/pybootchartgui.png](http://pybootchartgui.googlecode.com/svn/trunk/examples/1/pybootchartgui.png)
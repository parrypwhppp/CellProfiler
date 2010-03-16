"""
CellProfiler is distributed under the GNU General Public License.
See the accompanying file LICENSE for details.

Developed by the Broad Institute
Copyright 2003-2010

Please see the AUTHORS file for credits.

Website: http://www.cellprofiler.org
"""
__version__ = "$Revision$"

import sys
import os

# Mark's machine
if sys.platform.startswith('win'):
    try:
        import cellprofiler.cpmath.propagate
    except:
        print "Propagate module doesn't exist yet."
        print "CellProfiler will compile it, but may crash soon after."
        print "Restart CellProfiler and it will probably work."

if not hasattr(sys, 'frozen'):
    root = os.path.split(__file__)[0]
    if len(root) == 0:
        root = os.curdir
    root = os.path.abspath(root)
    site_packages = os.path.join(root, 'site-packages')
    if os.path.exists(site_packages) and os.path.isdir(site_packages):
        import site
        site.addsitedir(site_packages)

import optparse
usage = """usage: %prog [options] [<measurement-file>])
     where <measurement-file> is the optional filename for measurement output
           when running headless"""

parser = optparse.OptionParser(usage=usage)
parser.add_option("-p", "--pipeline",
                  dest="pipeline_filename",
                  help="Load this pipeline file on startup",
                  default=None)
parser.add_option("-c", "--run-headless",
                  action="store_false",
                  dest="show_gui",
                  default=True,
                  help="Run headless (without the GUI)")
parser.add_option("-r", "--run",
                  action="store_true",
                  dest="run_pipeline",
                  default=False,
                  help="Run the given pipeline on startup")
parser.add_option("-o", "--output-directory",
                  dest="output_directory",
                  default=None,
                  help="Make this directory the default output folder")
parser.add_option("-i", "--image-directory",
                  dest="image_directory",
                  default=None,
                  help="Make this directory the default input folder")
parser.add_option("-f", "--first-image-set",
                  dest="first_image_set",
                  default=None,
                  help="The one-based index of the first image set to process")
parser.add_option("-l", "--last-image-set",
                  dest="last_image_set",
                  default=None,
                  help="The one-based index of the last image set to process")
parser.add_option("-g", "--group",
                  dest="groups",
                  default=None,
                  help=('Restrict processing to one grouping in a grouped '
                        'pipeline. For instance, "-g ROW=H,COL=01", will '
                        'process only the group of image sets that match '
                        'the keys.'))
parser.add_option("--html",
                  action="store_true",
                  dest="output_html",
                  default = False,
                  help = "Output HTML help for all modules")

if not hasattr(sys, 'frozen'):
    parser.add_option("-b", "--do-not_build",
                      dest="build_extensions",
                      default=True,
                      action="store_false",
                      help="Do not build C and Cython extensions")
parser.add_option("-d", "--done-file",
                  dest="done_file",
                  default=None,
                  help=('The path to the "Done" file, written by CellProfiler'
                        ' shortly before exiting'))
parser.add_option("--measurements",
                  dest="print_measurements",
                  default=False,
                  action="store_true",
                  help="Open the pipeline file specified by the -p switch "
                  "and print the measurements made by that pipeline")
parser.add_option("--data-file",
                  dest="data_file",
                  default = None,
                  help = "Specify a data file for LoadData modules that "
                  'use the "From command-line" option')
options, args = parser.parse_args()

# necessary to prevent matplotlib trying to use Tkinter as its backend.
# has to be done before CellProfilerApp is imported
from matplotlib import use as mpluse
mpluse('WXAgg')

if (not hasattr(sys, 'frozen')) and options.build_extensions:
    import subprocess
    import cellprofiler.cpmath.setup
    import cellprofiler.utilities.setup
    import contrib.setup
    from distutils.dep_util import newer_group
    #
    # Check for dependencies and compile if necessary
    #
    compile_scripts = [(os.path.join('cellprofiler', 'cpmath', 'setup.py'),
                        cellprofiler.cpmath.setup),
                       (os.path.join('cellprofiler', 'utilities', 'setup.py'),
                        cellprofiler.utilities.setup),
                       (os.path.join('contrib', 'setup.py'),
                        contrib.setup)]
    current_directory = os.path.abspath(os.curdir)
    old_pythonpath = os.getenv('PYTHONPATH', None)

    # if we're using a local site_packages, the subprocesses will need
    # to be able to find it.
    if old_pythonpath:
        os.environ['PYTHONPATH'] = site_packages + ':' + old_pythonpath
    else:
        os.environ['PYTHONPATH'] = site_packages

    for compile_script, my_module in compile_scripts:
        script_path, script_file = os.path.split(compile_script)
        os.chdir(os.path.join(root, script_path))
        configuration = my_module.configuration()
        needs_build = False
        for extension in configuration['ext_modules']:
            target = extension.name + '.pyd'
            if newer_group(extension.sources, target):
                needs_build = True
        if not needs_build:
            continue
        if sys.platform == 'win32':
            p = subprocess.Popen(["python",
                                  script_file,
                                  "build_ext", "-i",
                                  "--compiler=mingw32"])
        else:
            p = subprocess.Popen(["python",
                                  script_file,
                                  "build_ext", "-i"])
        p.communicate()
    os.chdir(current_directory)
    if old_pythonpath:
        os.environ['PYTHONPATH'] = old_pythonpath
    else:
        del os.environ['PYTHONPATH']

if options.show_gui:
    from cellprofiler.cellprofilerapp import CellProfilerApp
    App = CellProfilerApp(0)

try:
    #
    # Important to go headless ASAP
    #
    import cellprofiler.preferences as cpprefs
    if not options.show_gui:
        cpprefs.set_headless()
        # What's there to do but run if you're running headless?
        # Might want to change later if there's some headless setup 
        if (not options.output_html) and (not options.print_measurements):
            options.run_pipeline = True
    
    if options.output_html:
        from cellprofiler.modules import output_module_html
        from cellprofiler.gui.help import output_gui_html
        # Write the individual topic files
        module_help_text  = output_module_html()
        nonmodule_help_text = output_gui_html()
        
        # Produce one html to unite them
        root = os.path.split(__file__)[0]
        if len(root) == 0:
            root = os.curdir
        webpage_path = os.path.join(root, 'cellprofiler', 'help')
        if not (os.path.exists(webpage_path) and os.path.isdir(webpage_path)):
            try:
                os.mkdir(webpage_path)
            except IOError:
                webpage_path = root
        index_fd = open(os.path.join(webpage_path,'index.html'),'w')
        
        #For some reason, Adobe doesn't like using absolute paths to assemble the PDF.
        #Also, Firefox doesn't like displaying the HTML image links using abs paths either.
        #So I have use relative ones. Should check this to see if works on the 
        #compiled version
        #path = os.path.split(os.path.abspath(sys.argv[0]))[0]
        #path = os.path.join(path, 'cellprofiler','icons')
        path = ".."
        path = os.path.join(path,'icons')
        LOCATION_COVERPAGE = os.path.join(path,'CPCoverPage.png')
        LOCATION_WHITEHEADLOGO = os.path.join(path,'WhiteheadInstituteLogo.png')
        LOCATION_CSAILLOGO = os.path.join(path,'CSAIL_Logo.png')
        LOCATION_IMAGINGPLATFORMBANNER  = os.path.join(path,'BroadPlusImagingPlusBanner.png')
        
        intro_text = """
<html style="font-family:arial">
<head>
<title>CellProfiler: Table of contents</title>
</head>
<body>
<div style="page-break-after:always"> 
<table width="100%%">
<tr><td align="center">
<img src="%(LOCATION_COVERPAGE)s" align="middle"></img>
</tr></td>
</table>
</div>
<div style="page-break-after:always"> 
<table width="100%%" cellpadding="10">
<tr><td align="middle"><b>CellProfiler</b> cell image analysis software</td></tr>
<tr><td align="middle"><b>Created by</b><br>Anne E. Carpenter and Thouis R. Jones</td></tr>
<tr><td align="middle"><b>In the laboratories of</b><br>David M. Sabatini and Polina Golland at</td></tr>
<tr><td align="middle"><img src="%(LOCATION_WHITEHEADLOGO)s"></img><img src="%(LOCATION_CSAILLOGO)s"></img></td></tr>
<tr><td align="middle">And now based at</td></tr>
<tr><td align="middle"><img src="%(LOCATION_IMAGINGPLATFORMBANNER)s"></img></td></tr>
<tr><td align="middle">
<b>CellProfiler is free and open-source!</b>

<p>If you find it useful, please credit CellProfiler in publications
<ol>
<li>Cite the website (www.cellprofiler.org)</li>
<li>Cite the publication (check the website for the citation).</li>
<li>Post the reference for your publication on the CellProfiler Forum (accessible 
from the website) so that we are aware of it.</li>
</ol></p>

<p>These steps will help us to maintain funding for the project and continue to 
improve and support it.</p>
</td></tr>
</table>
</div>
<h1>Table of contents</h1>"""%globals()
        index_fd.write(intro_text)
        index_fd.write(nonmodule_help_text)
        index_fd.write(module_help_text)
        index_fd.write("""</body></html>\n""")
        
        index_fd.close()
        
    if options.print_measurements:
        if options.pipeline_filename is None:
            raise ValueError("Can't print measurements, no pipeline file")
        import cellprofiler.pipeline as cpp
        pipeline = cpp.Pipeline()
        def callback(pipeline, event):
            if isinstance(event, cpp.LoadExceptionEvent):
                raise ValueError("Failed to load %s" % options.pipeline_filename)
        pipeline.add_listener(callback)
        pipeline.load(os.path.expanduser(options.pipeline_filename))
        columns = pipeline.get_measurement_columns()
        print "--- begin measurements ---"
        print "Object,Feature,Type"
        for object_name, feature, data_type in columns:
            print "%s,%s,%s" % (object_name, feature, data_type)
        print "--- end measurements ---"
    
    if options.data_file is not None:
        cpprefs.set_data_file(os.path.abspath(options.data_file))
        
    from cellprofiler.utilities.get_revision import version
    print "Subversion revision: %d"%version
    if options.run_pipeline and not options.pipeline_filename:
        raise ValueError("You must specify a pipeline filename to run")
    
    if not options.first_image_set is None:
        if not options.first_image_set.isdigit():
            raise ValueError("The --first-image-set option takes a numeric argument")
        else:
            image_set_start = int(options.first_image_set)
    else:
        image_set_start = None
    
    if not options.last_image_set is None:
        if not options.last_image_set.isdigit():
            raise ValueError("The --last-image-set option takes a numeric argument")
        else:
            image_set_end = int(options.last_image_set)
    else:
        image_set_end = None
    
    if options.output_directory:
        cpprefs.set_default_output_directory(options.output_directory)
    
    if options.image_directory:
        cpprefs.set_default_image_directory(options.image_directory)

    if options.show_gui:
        import cellprofiler.gui.cpframe as cpgframe
        if options.pipeline_filename:
            App.frame.pipeline.load(os.path.expanduser(options.pipeline_filename))
            if options.run_pipeline:
                App.frame.Command(cpgframe.ID_FILE_ANALYZE_IMAGES)
        App.MainLoop()
    elif options.run_pipeline:
        from cellprofiler.pipeline import Pipeline, EXIT_STATUS
        import cellprofiler.measurements as cpmeas
        pipeline = Pipeline()
        pipeline.load(os.path.expanduser(options.pipeline_filename))
        if options.groups is not None:
            kvs = [x.split('=') for x in options.groups.split(',')]
            groups = dict(kvs)
        else:
            groups = None
        measurements = pipeline.run(image_set_start=image_set_start, 
                                    image_set_end=image_set_end,
                                    grouping=groups)
        if len(args) > 0:
            pipeline.save_measurements(args[0], measurements)
        if options.done_file is not None:
            if (measurements is not None and 
                measurements.has_feature(cpmeas.EXPERIMENT, EXIT_STATUS)):
                done_text = measurements.get_experiment_measurement(EXIT_STATUS)
            else:
                done_text = "Failure"
            fd = open(options.done_file, "wt")
            fd.write("%s\n"%done_text)
            fd.close()
finally:
    try:
        import cellprofiler.utilities.jutil as jutil
        jutil.kill_vm()
    except:
        import traceback
        traceback.print_exc()
        print "Caught exception while killing VM"
import os


import subprocess
import tempfile

import nbformat

_TEST_DIR = os.path.dirname(__file__)

_EXCLUDE = ['Python_intro.ipynb']

def _notebook_run(path):
    """Execute a notebook via nbconvert and collect output.
       :returns (parsed nb object, execution errors)
    """
    dirname, __ = os.path.split(path)
    os.chdir(dirname)
    with tempfile.NamedTemporaryFile(suffix=".ipynb") as fout:
        args = ["jupyter", "nbconvert", "--to", "notebook", "--execute",
          "--ExecutePreprocessor.kernel_name=python",
          "--ExecutePreprocessor.timeout=None",
          "ExecutePreprocessor.iopub_timeout=100",
          "--output", fout.name, path]
        subprocess.check_call(args)

        fout.seek(0)
        nb = nbformat.read(fout, nbformat.current_nbformat)

    errors = [output for cell in nb.cells if "outputs" in cell
                     for output in cell["outputs"]\
                     if output.output_type == "error"]

    return nb, errors


def test_tutorial_template():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "tutorial_template.ipynb"))
    assert errors == []


def test_gradient_and_divergence():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "gradient_and_divergence/gradient_and_divergence.ipynb"))
    assert errors == []


def test_component_tutorial():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "component_tutorial/component_tutorial.ipynb"))
    assert errors == []


def test_landlab_fault_scarp():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "fault_scarp/landlab-fault-scarp.ipynb"))
    assert errors == []


def test_TLHDiff_tutorial():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "transport-length_hillslope_diffuser/TLHDiff_tutorial.ipynb"))
    assert errors == []


def test_the_FlowDirectors():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "flow_direction_and_accumulation/the_FlowDirectors.ipynb"))
    assert errors == []


def test_compare_FlowDirectors():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "flow_direction_and_accumulation/compare_FlowDirectors.ipynb"))
    assert errors == []


def test_the_FlowAccumulator():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "flow_direction_and_accumulation/the_FlowAccumulator.ipynb"))
    assert errors == []


def test_overland_flow_driver():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "overland_flow/overland_flow_driver.ipynb"))
    assert errors == []


def test_making_components():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "making_components/making_components.ipynb"))
    assert errors == []


def test_landlab_plotting():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "plotting/landlab-plotting.ipynb"))
    assert errors == []


# this notebook not tested because it requires FFMPEG
# def test_animate_landlab_output():
#     nb, errors = _notebook_run(os.path.join(_TEST_DIR, "plotting/animate-landlab-output.ipynb"))
#     assert errors == []


def test_grid_object_demo():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "grid_object_demo/grid_object_demo.ipynb"))
    assert errors == []


def test_normal_fault_component_tutorial():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "normal_fault/normal_fault_component_tutorial.ipynb"))
    assert errors == []


def test_working_with_fields():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "fields/working_with_fields.ipynb"))
    assert errors == []


def test_mappers():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "mappers/mappers.ipynb"))
    assert errors == []


def test_flexure_1d():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "flexure/flexure_1d.ipynb"))
    assert errors == []


def test_lots_of_loads():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "flexure/lots_of_loads.ipynb"))
    assert errors == []


def test_set_BCs_on_raster_perimeter():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "boundary_conds/set_BCs_on_raster_perimeter.ipynb"))
    assert errors == []


def test_set_BCs_from_xy():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "boundary_conds/set_BCs_from_xy.ipynb"))
    assert errors == []


def test_set_watershed_BCs_raster():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "boundary_conds/set_watershed_BCs_raster.ipynb"))
    assert errors == []


def test_set_BCs_on_voronoi():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "boundary_conds/set_BCs_on_voronoi.ipynb"))
    assert errors == []


# def test_lithology_and_litholayers(): # this doesn't exist on this branch yet
#     nb, errors = _notebook_run(os.path.join(_TEST_DIR, "lithology/lithology_and_litholayers.ipynb"))
#     assert errors == []


def test_reading_dem_into_landlab():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "reading_dem_into_landlab/reading_dem_into_landlab.ipynb"))
    assert errors == []


def test_application_of_flow__distance_utility():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "flow__distance_utility/application_of_flow__distance_utility.ipynb"))
    assert errors == []


def test_cellular_automaton_vegetation_flat_domain():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "ecohydrology/cellular_automaton_vegetation_flat_surface/cellular_automaton_vegetation_flat_domain.ipynb"))
    assert errors == []


def test_cellular_automaton_vegetation_DEM():
    nb, errors = _notebook_run(os.path.join(_TEST_DIR, "ecohydrology/cellular_automaton_vegetation_DEM/cellular_automaton_vegetation_DEM.ipynb"))
    assert errors == []


# def test_Python_intro():
#     nb, errors = _notebook_run(os.path.join(_TEST_DIR, "python_intro/Python_intro.ipynb"))
#     assert errors == []


# def test_all_ipynbs():
#     failed = []
#     to_run = []
#
#     for root, dirs, files in os.walk(_TEST_DIR):
#         for file in files:
#             if (file.endswith('.ipynb') and (file not in _EXCLUDE) and ('checkpoint' not in file)):
#                 to_run.append(os.path.join(root, file))
#     for fp in to_run:
#         print('STARTING: '+os.path.split(fp)[-1])
#         nb, errors = _notebook_run(os.path.join(fp))
#         try:
#             assert errors == []
#             print('PASSED : '+file)
#         except AssertionError:
#             print('FAILED : '+file)
#             print(errors)
#             failed.append(file)
#         except:
#             failed.append(file)
#
#     print(str(len(failed)) + ' notebooks failed')
#     for fnb in failed:
#         print(fnb)
#     assert failed == []

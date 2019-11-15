from app_common.chaco.plot_io import save_plot_to_file

from chaco.api import Plot, ArrayPlotData
from chaco.api import PlotGraphicsContext
from chaco.pdf_graphics_context import PdfPlotGraphicsContext
from chaco.tools.api import SaveTool

data = {"x": [1, 2, 3, 4, 5], "y": [1, 2, 3, 2, 1]}

plot = Plot(ArrayPlotData(**data))

plot.plot(("x", "y"), type="scatter", color="blue")

plot.padding = 20
plot.outer_bounds = (800, 600)
plot.do_layout(force=True)

gc = PlotGraphicsContext((800, 600), dpi=72)
gc.render_component(plot, container_coords=(10, 10))
gc.save("test1.PNG")

# save_plot_to_file(plot, "test1.PNG")
# save_plot_to_file(plot, "test2.PNG")

# gc = PlotGraphicsContext((800, 600), dpi=72)
# plot.draw(gc)
# gc.save("test1.JPG")

# gc = PdfPlotGraphicsContext(filename="test1.PDF",
#                             pagesize="letter",
#                             dest_box=(0.5, 0.5, -0.5, -0.5),
#                             dest_box_units="inch")
# gc.render_component(plot)
# gc.save()

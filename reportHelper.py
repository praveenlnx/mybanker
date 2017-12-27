from flask import current_app as app
import pygal
import calendar
from pygal.style import LightColorizedStyle
from dbHelper import getInEx, getExpenseStats, getCategoryStats, getDetailedCategoryStats

# Generate bar chart for income/expense for the selected year
def inexTrend(username, year):
  chart = pygal.Bar(legend_at_bottom=True, show_y_labels=False, pretty_print=True, tooltip_border_radius=10, height=750)
  chart.x_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  income_data = []
  expense_data = []
  inexdata = getInEx(username, year)
  if not inexdata is None:
    for row in inexdata:
      income_data.append(row[1])
      expense_data.append(row[2])
    chart.add('Income', income_data)
    chart.add('Expense', expense_data)
  else:
    chart.add('line', [])
  return chart.render_data_uri()

# Generate pie chart for expense stats for the selected year
def expenseStats(username, year):
  chart = pygal.Pie(legend_at_bottom=True, tooltip_border_radius=10, height=750)
  expensedata = getExpenseStats(username, year)
  if not expensedata is None:
    for row in expensedata:
      chart.add(row[0], row[1])
  else:
    chart.add('line',[])
  return chart.render_data_uri()

# Generate bar chart for expense stats for the selected year
def expenseStatsBar(username, year):
  chart = pygal.HorizontalBar(legend_at_bottom=True, tooltip_border_radius=10, height=750)
  expensedata = getExpenseStats(username, year)
  if not expensedata is None:
    for row in expensedata:
      chart.add(row[0], row[1])
  else:
    chart.add('line',[])
  return chart.render_data_uri()

# Generate line chart for income expense trend since beginning for a user
def inexTrendAll(username):
  chart = pygal.Line(legend_at_bottom=True, interpolate="hermite", pretty_print=True, tooltip_border_radius=10, fill=True, height=400, style=LightColorizedStyle, dots_size=1, x_label_rotation=270)
  income_data = []
  expense_data = []
  labelSeries = []
  inexAllData = getInEx(username, None, "all")
  if not inexAllData is None:
    for row in inexAllData:
      (year,month) = (str(row[0])[:4], str(row[0])[4:])
      labelSeries.append("%s %s" % (year, calendar.month_abbr[int(month)]))
      income_data.append(row[1])
      expense_data.append(row[2])
    chart.x_labels = labelSeries
    chart.add('Income', income_data)
    chart.add('Expense', expense_data)
  else:
    chart.add('line', [])
  return chart.render_data_uri()

# Generate line chart for category
def categoryStats(username, category, period="YEAR_MONTH"):
  chart = pygal.Line(tooltip_border_radius=10, interpolate="hermite", fill=True, style=LightColorizedStyle, height=350, dot_size=1, x_label_rotation=270, show_legend=False)
  periodAbr = "Yearly"
  periodAbr = "Monthly" if "MONTH" in period else periodAbr
  chart.title = "(%s) Stats for category: %s" % (periodAbr, category)
  dataSeries = []
  labelSeries = []
  statsdata = None
  data = getCategoryStats(username, category, period)
  if not data is None:
    statsdata = getDetailedCategoryStats(data, period)
    for row in data:
      if period == "YEAR_MONTH":
        (year,month) = (str(row[0])[:4], str(row[0])[4:])
        labelSeries.append("%s %s" % (year, calendar.month_abbr[int(month)]))
      else:
        labelSeries.append(row[0])
      dataSeries.append(row[1])
    chart.x_labels = labelSeries
    maxY = int(max(dataSeries))
    maxYRounded = (int(maxY / 100) + 1) * 100
    chart.y_labels = [0, maxYRounded]
    chart.add(category, dataSeries)
  else:
    chart.add('line',[])  
  return chart.render_data_uri(), statsdata

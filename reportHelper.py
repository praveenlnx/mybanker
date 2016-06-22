from flask import current_app as app
import pygal
from pygal.style import LightColorizedStyle
from dbHelper import getInEx, getExpenseStats, getCategoryStats, getDetailedCategoryStats

# Generate bar chart for income/expense for the selected year
def inexTrend(username, year):
  chart = pygal.Bar(legend_at_bottom=True, show_y_labels=False, pretty_print=True, tooltip_border_radius=10)
  chart.title = "Income/Expense Trend for %s" % year
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
  chart = pygal.Pie(legen_at_bottom=True, tooltip_border_radius=10)
  chart.title = "Expense stats for %s" % year
  expensedata = getExpenseStats(username, year)
  if not expensedata is None:
    for row in expensedata:
      chart.add(row[0], row[1])
  else:
    chart.add('line',[])
  return chart.render_data_uri()

# Generate line chart for income expense trend since beginning for a user
def inexTrendAll(username):
  chart = pygal.Line(legend_at_bottom=True, interpolate='cubic', pretty_print=True, tooltip_border_radius=10, fill=True, height=400, style=LightColorizedStyle, dots_size=1)
  income_data = []
  expense_data = []
  inexAllData = getInEx(username, None, "all")
  if not inexAllData is None:
    for row in inexAllData:
      income_data.append(row[1])
      expense_data.append(row[2])
    chart.add('Income', income_data)
    chart.add('Expense', expense_data)
  else:
    chart.add('line', [])
  return chart.render_data_uri()

# Generate line chart for category
def categoryStats(username, category):
  chart = pygal.Line(legend_at_bottom=True, interpolate='cubic', tooltip_border_radius=10, fill=True, style=LightColorizedStyle, height=350, dot_size=1)
  chart.title = "Stats for category: %s" % category
  dataSeries = []
  statsdata = None
  data = getCategoryStats(username, category)
  if not data is None:
    statsdata = getDetailedCategoryStats(data)
    for row in data:
      dataSeries.append(row[1])
    chart.add(category, dataSeries)
  else:
    chart.add('line',[])  
  return chart.render_data_uri(), statsdata

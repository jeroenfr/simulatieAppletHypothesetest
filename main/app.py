from shiny.express import input, render, ui
from shiny import reactive
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd

#DEFINITION OF CONSTANTS
MAX_SIMS = 1000000;
TEST_TYPES = {"right": "Eenzijdig rechts", "left": "Eenzijdig links", "twosided": "Tweezijdig"}

ui.page_opts(title="Toetsen van hypotheses met simulaties - applet")

with ui.sidebar(width=400):
    ui.markdown("<strong>Instellingen simulatie</strong>");
    #USER INPUT ELEMENTS
    ui.input_numeric("sampleSize", "Steekproefgrootte n",value=500,min=100,max=10000);
    ui.input_slider("observedProportion", "Geobserveerde steekproefproportie p\u0302", value=0.32, min=0, max=1, step=0.005);
    ui.input_slider("nullHypothesis", "Nulhypothese p\u2080", value=0.3, min=0, max=1, step=0.005);
    ui.input_numeric("simulationSize", "Aantal simulaties onder de nulhypothese",value=10000,min=1,max=MAX_SIMS,step=1);
    ui.input_radio_buttons("testType", "Type van de test:", TEST_TYPES, selected="right", inline=False)
    ui.markdown("<strong>Visualisatie instellingen</strong>");
    ui.input_checkbox("showThreshold", "Toon drempelwaarde op de histogrammen",value=False);
    ui.input_switch("useProportions", "Gebruik proporties",False);

ui.markdown("<strong>Resultaten simulatie</strong>");

#INTERMEDIATE ELEMENTS
#Create a number generator with seed 1
rng = np.random.default_rng(1);
#Generate random data with default settings and put in reactive variable
results = reactive.value(rng.binomial(500, 0.3, MAX_SIMS));
#Select subset of generated data according to default value of simulationSize and put in reactive value
selectedResults = reactive.value(results._value[0:10000]);

@reactive.effect
def updateData():
  try:
    sampleSize = int(input.sampleSize());
    if sampleSize < 100:
      sampleSize=100;
  except:
    sampleSize = 100; #Default value when sampleSize is left empty
  nullHypothesis = input.nullHypothesis();
  results.set(rng.binomial(sampleSize, nullHypothesis, MAX_SIMS));
  
@reactive.effect
def selectSubsetData():
  simulationSize = input.simulationSize();
  resultsData = results.get();
  selectedResults.set(resultsData[0:simulationSize]);

#OUTPUT ELEMENTS
@render.plot(alt="A histogram")
def showHistogram():
  sampleSize = input.sampleSize();
  if sampleSize < 100:
      sampleSize=100;
  observedProportion = input.observedProportion();
  showCutoffLine = input.showThreshold();
  nullHypothesis = input.nullHypothesis();

  selectedResultsData = selectedResults.get();

  binWidth = 1; #one bar for each number

  #Make figure
  fig, (ax1,ax2) = plt.subplots(1,2,figsize=(10,5));
  bins = np.arange(0,sampleSize,binWidth);
  N, bins, patches = ax1.hist(selectedResultsData,bins=bins,rwidth=0.75,align='left')

  for i in range(0,np.size(bins)-1):
    match input.testType():
      case 'right':
        if bins[i]>=observedProportion*sampleSize:
          patches[i].set_facecolor('orange')
      case 'left':
        if bins[i]<=observedProportion*sampleSize:
          patches[i].set_facecolor('orange')
      case 'twosided':
        distance = abs(nullHypothesis - observedProportion)
        leftThreshold = round(sampleSize*(nullHypothesis - distance));
        rightThreshold = round(sampleSize*(nullHypothesis + distance));
        if not(bins[i] >= leftThreshold and bins[i]<= rightThreshold):
          patches[i].set_facecolor('orange')

  if showCutoffLine:
    match input.testType():
      case 'twosided':
        ax1.vlines(leftThreshold,0,1.1*max(N),color='red',linestyles='dashed');
        ax1.vlines(rightThreshold,0,1.1*max(N),color='red',linestyles='dashed');
      case other:
        ax1.vlines(observedProportion*sampleSize,0,1.1*max(N),color='red',linestyles='dashed');
  
  ax1.set_title('Uitgezoomd')
  ax1.set_xlabel('Aantal successen in een enkele steekproef (X)');
  ax1.set_xlim(0,sampleSize);
  if (input.useProportions()):
    ax1.xaxis.set_major_formatter(mtick.PercentFormatter(sampleSize))
  ax1.set_ylabel('Frequentie');
  ax1.set_ylim(0,1.1*max(N));

  minimumResult = min(selectedResultsData)-10;
  maximumResult = max(selectedResultsData)+10;
  bins = np.arange(minimumResult,maximumResult,binWidth);
  N, bins, patches = ax2.hist(selectedResultsData,bins=bins,rwidth=0.75,align='left');

  for i in range(0,np.size(bins)-1):
    match input.testType():
      case 'right':
        if bins[i]>=observedProportion*sampleSize:
          patches[i].set_facecolor('orange')
      case 'left':
        if bins[i]<=observedProportion*sampleSize:
          patches[i].set_facecolor('orange')
      case 'twosided':
        distance = abs(nullHypothesis - observedProportion)
        leftThreshold = round(sampleSize*(nullHypothesis - distance));
        rightThreshold = round(sampleSize*(nullHypothesis + distance));
        if not(bins[i] > leftThreshold and bins[i] < rightThreshold):
          patches[i].set_facecolor('orange')

  if showCutoffLine:
    match input.testType():
      case 'twosided':
        ax2.vlines(leftThreshold,0,1.1*max(N),color='red',linestyles='dashed');
        ax2.vlines(rightThreshold,0,1.1*max(N),color='red',linestyles='dashed');
      case other:
        ax2.vlines(observedProportion*sampleSize,0,1.1*max(N),color='red',linestyles='dashed');
  
  ax2.set_title('Ingezoomd')
  ax2.set_xlabel('Aantal successen in een enkele steekproef (X)');
  ax2.set_xlim(minimumResult,maximumResult);
  if (input.useProportions()):
    ax2.xaxis.set_major_formatter(mtick.PercentFormatter(sampleSize))
  ax2.set_ylabel('Frequentie');
  ax2.set_ylim(0,1.1*max(N));

  plt.suptitle('Histogrammen van de steekproevenverdeling');
  return fig

with ui.card():
  ui.card_header("Drempelwaarde(n)")
  @render.ui
  def calculateThresholdValue():
    sampleSize = input.sampleSize();
    if sampleSize < 100:
      sampleSize=100;
    observedProportion = input.observedProportion();
    nullHypothesis = input.nullHypothesis();
    threshold = np.round(sampleSize*observedProportion,2);
    if "left" in input.testType():
        x = ui.p('X \u2264' + str(threshold))
    if "right" in input.testType():
        x = ui.p('X \u2265' + str(threshold))
    if "twosided" in input.testType():
      distance = abs(nullHypothesis - observedProportion)
      leftThreshold = round(sampleSize*(nullHypothesis - distance));
      rightThreshold = round(sampleSize*(nullHypothesis + distance));
      x = ui.p('X \u2264' + str(int(leftThreshold)) + ' of X \u2265 ' + str(int(rightThreshold)))
    return x

with ui.card():
  ui.card_header("Empirische p-waarde");
  @render.ui
  def calculateEmpiricalPvalue():
    sampleSize = input.sampleSize();
    if sampleSize < 100:
      sampleSize=100;
    simulationSize = input.simulationSize();
    if simulationSize > MAX_SIMS:
      simulationSize = MAX_SIMS;
    observedProportion = input.observedProportion();
    nullHypothesis = input.nullHypothesis();
    selectedResultsData = selectedResults.get();

    threshold = np.round(sampleSize*observedProportion,2);
    if "left" in input.testType():
        nbLargerSampleProportions = np.count_nonzero(selectedResultsData[selectedResultsData<=observedProportion*sampleSize])
        x = ui.p(str(nbLargerSampleProportions) + '/' + str(simulationSize) + '=' + str(np.round(nbLargerSampleProportions/simulationSize,4)));
    if "right" in input.testType():
        nbLargerSampleProportions = np.count_nonzero(selectedResultsData[selectedResultsData>=observedProportion*sampleSize])
        x = ui.p(str(nbLargerSampleProportions) + '/' + str(simulationSize) + '=' + str(np.round(nbLargerSampleProportions/simulationSize,4)));
    if "twosided" in input.testType():
      distance = abs(nullHypothesis - observedProportion)
      leftThreshold = round(sampleSize*(nullHypothesis - distance));
      rightThreshold = round(sampleSize*(nullHypothesis + distance));
      nbLargerSampleProportions = np.count_nonzero(selectedResultsData[selectedResultsData>=rightThreshold])
      nbSmallerSampleProportions = np.count_nonzero(selectedResultsData[selectedResultsData<=leftThreshold])
      x = ui.p(str(int(nbLargerSampleProportions+nbSmallerSampleProportions)) + '/' + str(simulationSize) + '=' + str(np.round((nbSmallerSampleProportions+nbLargerSampleProportions)/simulationSize,4)));
    return x
  
with ui.accordion(id="acc", open=False,):  
  with ui.accordion_panel("Tabel met simulatiedata"):  
    @render.data_frame  
    def showTable():
      sampleSize = input.sampleSize();
      if sampleSize < 100:
        sampleSize=100;
      nullHypothesis = input.nullHypothesis();
      observedProportion = input.observedProportion();

      my_array = np.zeros((input.simulationSize(),4));
      my_array[0:,0] = np.arange(1,np.size(selectedResults.get())+1);
      my_array[0:,1] = selectedResults.get();
      my_array[0:,2] = selectedResults.get()/sampleSize;
      if "left" in input.testType():
        my_array[0:,3] = selectedResults.get()<=(observedProportion*sampleSize);
      if "right" in input.testType():
        my_array[0:,3] = selectedResults.get()>=(observedProportion*sampleSize);
      if "twosided" in input.testType():
        distance = abs(nullHypothesis - observedProportion)
        leftThreshold = round(sampleSize*(nullHypothesis - distance));
        rightThreshold = round(sampleSize*(nullHypothesis + distance));
        my_array[0:,3] = np.logical_or(selectedResults.get() <= leftThreshold, selectedResults.get() >= rightThreshold)

      df = pd.DataFrame(my_array, columns=['Simulatie nummer','# successen','Proportie','Drempelwaarde overschreden?'])
      return render.DataGrid(df)
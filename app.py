from shiny.express import input, render, ui, suspend_display
from shiny import reactive
import math
import numpy as np
import matplotlib.pyplot as plt

#DEFINITION OF CONSTANTS
MAX_SIMS = 1000000;
#NB_OF_BINS = 100; #This value should be tuned for optimal visualisation of histograms

ui.page_opts(title="Toetsen van hypotheses met simulaties - applet")

with ui.sidebar(width=400):
    ui.markdown("<strong>Instellingen</strong>");
    #USER INPUT ELEMENTS
    ui.input_numeric("sampleSize", "Steekproefgrootte n",value=500,min=1,max=100000);
    ui.input_slider("observedProportion", "Geobserveerde steekproefproportie p\u0302", value=0.32, min=0, max=1);
    ui.input_slider("nullHypothesis","Nulhypothese p\u2080", value=0.3, min=0, max=1);
    ui.input_numeric("simulationSize", "Aantal simulaties onder de nulhypothese",value=1000,min=1,max=MAX_SIMS,step=50);
    ui.input_checkbox("showThreshold", "Toon drempelwaarde op de histogrammen",value=False);
    ui.input_switch("useProportions","Gebruik proporties",False);

ui.markdown("<strong>Simulatieresultaten</strong>");

#INTERMEDIATE ELEMENTS
#Create a number generator with seed 1
rng = np.random.default_rng(1);
#Generate random data with default settings and put in reactive variable
results = reactive.value(rng.binomial(500, 0.3, MAX_SIMS));
#Select subset of generated data according to default value of simulationSize and put in reactive value
selectedResults = reactive.value(results._value[0:1000]);

@reactive.effect
def updateData():
  try:
    sampleSize = int(input.sampleSize());
  except:
    sampleSize = 1; #Default value when sampleSize is left empty
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
  observedProportion = input.observedProportion();
  showCutoffLine = input.showThreshold();

  selectedResultsData = selectedResults.get();

  binWidth = 1; #one bar for each number
  if (input.useProportions()):
    selectedResultsData = selectedResultsData/sampleSize;
    #binWidth = binWidth/sampleSize; #This gives undesired numerical artifacts
    binWidth = 0.01; #one bar for each percent
    sampleSize = 1;

  #Make figure
  fig, (ax1,ax2) = plt.subplots(1,2,figsize=(10,5));
  bins = np.arange(0,sampleSize,binWidth);
  N, bins, patches = ax1.hist(selectedResultsData,bins=bins,rwidth=0.75)

  for i in range(0,np.size(bins)-1):
    if (bins[i]+bins[i+1])/2>observedProportion*sampleSize:
      patches[i].set_facecolor('orange')
  if showCutoffLine:
    ax1.vlines(observedProportion*sampleSize,0,1.1*max(N),color='red',linestyles='dashed');
  
  ax1.set_title('Uitgezoomd')
  ax1.set_xlabel('Aantal successen in een enkele steekproef');
  ax1.set_xlim(0,sampleSize);
  ax1.set_ylabel('Frequentie');
  ax1.set_ylim(0,1.1*max(N));

  minimumResult = min(selectedResultsData);
  maximumResult = max(selectedResultsData);
  bins = np.arange(minimumResult,maximumResult,binWidth);
  N, bins, patches = ax2.hist(selectedResultsData,bins=bins,rwidth=0.75);

  for i in range(0,np.size(bins)-1):
    if (bins[i]+bins[i+1])/2>observedProportion*sampleSize:
      patches[i].set_facecolor('orange')
  if showCutoffLine:
    ax2.vlines(observedProportion*sampleSize,0,1.1*max(N),color='red',linestyles='dashed');
  
  ax2.set_title('Ingezoomd')
  ax2.set_xlabel('Aantal successen in een enkele steekproef');
  ax2.set_xlim(minimumResult,maximumResult);
  ax2.set_ylabel('Frequentie');
  ax2.set_ylim(0,1.1*max(N));

  plt.suptitle('Histogrammen van de steekproevenverdeling');
  return fig

with ui.card():
  ui.card_header("Drempelwaarde")
  @render.text
  def calculateThresholdValue():
    sampleSize = input.sampleSize();
    observedProportion = input.observedProportion();
    return f"{np.round(sampleSize*observedProportion,2)}"

with ui.card():
  ui.card_header("Empirische p-waarde");
  @render.text
  def calculateEmpiricalPvalue():
    sampleSize = input.sampleSize();
    simulationSize = input.simulationSize();
    if simulationSize > MAX_SIMS:
      simulationSize = MAX_SIMS;
    observedProportion = input.observedProportion();
    selectedResultsData = selectedResults.get();
    nbLargerSampleProportions = np.count_nonzero(selectedResultsData[selectedResultsData>observedProportion*sampleSize])
    return f"{nbLargerSampleProportions}/{simulationSize} = {np.round(nbLargerSampleProportions/simulationSize,4)}"
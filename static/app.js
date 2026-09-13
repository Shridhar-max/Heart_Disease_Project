const form = document.querySelector('#predictionForm');
const resultPanel = document.querySelector('#resultPanel');
const resultTitle = document.querySelector('#resultTitle');
const resultMessage = document.querySelector('#resultMessage');
const probability = document.querySelector('#probability');
const resetButton = document.querySelector('#resetButton');
const printButton = document.querySelector('#printButton');
const autofillButton = document.querySelector('#autofillButton');
const themeToggle = document.querySelector('#themeToggle');
const authNavLink = document.querySelector('#authNavLink');
const readStoredJson = (key, fallback) => {
  try {
    const value = localStorage.getItem(key);
    return value ? JSON.parse(value) : fallback;
  } catch (error) {
    localStorage.removeItem(key);
    return fallback;
  }
};
if (authNavLink && localStorage.getItem('heartpredict_session') === 'true') {
  authNavLink.href = '/login';
  authNavLink.textContent = 'Logout';
  authNavLink.addEventListener('click', (event) => {
    event.preventDefault();
    localStorage.removeItem('heartpredict_session');
    window.location.href = '/login';
  });
}
const randomValue = (minimum, maximum, decimals = 0) => {
  const scale = 10 ** decimals;
  return Math.round((minimum + Math.random() * (maximum - minimum)) * scale) / scale;
};
const createDemoProfile = () => ({
  age: randomValue(25, 85), sex: Math.random() < 0.5 ? 'Male' : 'Female',
  systolic_bp: randomValue(105, 180), diastolic_bp: randomValue(65, 115),
  resting_heart_rate: randomValue(50, 120), body_temperature: randomValue(97.2, 100.4, 1),
  total_cholesterol: randomValue(130, 320, 1), ldl_cholesterol: randomValue(55, 220, 1),
  hdl_cholesterol: randomValue(30, 85, 1), blood_glucose: randomValue(70, 210, 1),
  serum_creatinine: randomValue(0.5, 2.5, 2), crp: randomValue(0.2, 15, 2),
  wbc_count: randomValue(3.5, 15, 1), pr_interval: randomValue(180, 260),
  qt_interval: randomValue(300, 500), qtc_interval: randomValue(330, 550),
  heart_axis: randomValue(-60, 150), ejection_fraction: randomValue(25, 75),
  ea_ratio: randomValue(0.4, 2, 2), wmsi: randomValue(1, 2.4, 2),
  bmi: randomValue(18, 42, 1), smoking_cigarettes: randomValue(0, 25),
  alcohol_ml: randomValue(0, 250), parent_disease: Math.random() < 0.5 ? 'None' : 'Yes'
});
const evidenceList = document.querySelector('#evidenceList');
const setMetric = (id, value, suffix = '') => { const element = document.querySelector(`#${id}`); if (element) element.textContent = value == null ? '--' : `${(Number(value) * 100).toFixed(1)}${suffix}`; };
const setBar = (id, value) => { const element = document.querySelector(`#${id}`); if (element) element.style.width = `${Math.max(0, Math.min(100, Number(value) * 100))}%`; };

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  button.innerHTML = 'Reading pattern <span class="spinner"></span>';
  const payload = Object.fromEntries(new FormData(form).entries());
  try {
    const response = await fetch('/api/predict', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
    const responseText = await response.text();
    let result;
    try {
      result = responseText ? JSON.parse(responseText) : {};
    } catch (error) {
      throw new Error(`The server returned an invalid response (${response.status}).`);
    }
    if (!response.ok) throw new Error(result.error || 'Unable to analyze this profile.');
    const isHigher = result.risk === 'higher';
    resultPanel.hidden = false;
    resultPanel.classList.toggle('higher-risk', isHigher);
    resultTitle.textContent = `Predicted class: ${result.disease}`;
    resultMessage.textContent = `${result.message} ${result.source === 'trained model' ? 'This result comes from the trained workbook model.' : 'Add a labeled dataset and train the model to replace this early screening estimate.'}`;
    probability.textContent = `${result.probability}%`;
    if (evidenceList) evidenceList.innerHTML = (result.based_on || []).map(item => `<li><span>${item.name}<small>${item.value}</small></span><i><em style="width:${Math.max(8, item.importance * 4)}%"></em></i><b>${item.importance}%</b></li>`).join('') || '<li>Model explanation is unavailable for this estimate.</li>';
    let classBreakdown = document.querySelector('#classBreakdown');
    if (!classBreakdown && evidenceList) {
      evidenceList.insertAdjacentHTML('afterend', '<div class="class-breakdown"><h3>All class probabilities</h3><div id="classBreakdown"></div></div>');
      classBreakdown = document.querySelector('#classBreakdown');
    }
    if (classBreakdown) classBreakdown.innerHTML = (result.class_probabilities || []).map(item => `<div class="class-probability"><span>${item.name}</span><i><em style="width:${item.probability}%"></em></i><b>${item.probability}%</b></div>`).join('');
    const metrics = result.metrics || {};
    const metricGrid = document.querySelector('.metric-grid');
    if (metricGrid && !document.querySelector('#recallMetric')) {
      metricGrid.insertAdjacentHTML('beforeend', '<div><b id="recallMetric">--</b><small>Recall</small></div>');
    }
    setMetric('accuracyMetric', metrics.accuracy, '%');
    setMetric('precisionMetric', metrics.precision, '%');
    setMetric('recallMetric', metrics.recall, '%');
    setMetric('f1Metric', metrics.f1, '%');
    const lossElement = document.querySelector('#lossMetric');
    if (lossElement) lossElement.textContent = metrics.loss == null ? '--' : Number(metrics.loss).toFixed(3);
    setBar('accuracyBar', metrics.accuracy);
    setBar('precisionBar', metrics.precision);
    setBar('recallBar', metrics.recall);
    setBar('f1Bar', metrics.f1);
    setBar('lossBar', metrics.loss);
    const currentUser = readStoredJson('heartpredict_user', null);
    const historyKey = `heartpredict_history_${encodeURIComponent(currentUser?.email || 'guest')}`;
    const history = readStoredJson(historyKey, []);
    history.unshift({ disease: result.disease, probability: result.probability, risk: result.risk, date: new Date().toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) });
    localStorage.setItem(historyKey, JSON.stringify(history.slice(0, 10)));
    resultPanel.scrollIntoView({ behavior: 'smooth', block: 'center' });
  } catch (error) {
    resultPanel.hidden = false;
    resultTitle.textContent = 'We need one more try.';
    resultMessage.textContent = error.message;
    probability.textContent = '--';
  } finally {
    button.disabled = false;
    button.innerHTML = 'Analyze risk <span>↗</span>';
  }
});

resetButton.addEventListener('click', () => { resultPanel.hidden = true; form.reset(); window.scrollTo({top: 0, behavior: 'smooth'}); });
printButton.addEventListener('click', () => window.print());
autofillButton.addEventListener('click', () => {
  const profile = createDemoProfile();
  Object.entries(profile).forEach(([name, value]) => { form.elements[name].value = value; });
  autofillButton.textContent = 'New demo values added';
  window.setTimeout(() => { autofillButton.textContent = 'Auto-fill demo values'; }, 1600);
});
themeToggle.addEventListener('click', () => document.body.classList.toggle('light-mode'));

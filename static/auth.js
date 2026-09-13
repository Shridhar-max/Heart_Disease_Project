const userKey = 'heartpredict_user';
const sessionKey = 'heartpredict_session';
const historyKey = 'heartpredict_history';
const noticeKey = 'heartpredict_auth_notice';
const getUser = () => JSON.parse(localStorage.getItem(userKey) || 'null');
const getHistoryKey = () => `${historyKey}_${encodeURIComponent(getUser()?.email || 'guest')}`;

const registerForm = document.querySelector('#registerForm');
if (registerForm) registerForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(registerForm).entries());
  const existing = getUser();
  if (existing?.email === data.email) {
    document.querySelector('#registerError').textContent = 'An account with this email already exists. Please login.';
    return;
  }
  localStorage.setItem(userKey, JSON.stringify({name: data.name, email: data.email, password: data.password}));
  localStorage.removeItem(sessionKey);
  localStorage.setItem(noticeKey, 'Registration successful. Please login to continue.');
  window.location.href = '/login';
});

const loginForm = document.querySelector('#loginForm');
const loginNotice = localStorage.getItem(noticeKey);
if (loginForm && loginNotice) {
  const notice = document.createElement('p');
  notice.className = 'auth-notice';
  notice.textContent = loginNotice;
  loginForm.parentElement.insertBefore(notice, loginForm);
  localStorage.removeItem(noticeKey);
}
if (loginForm) loginForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const saved = getUser();
  const data = Object.fromEntries(new FormData(loginForm).entries());
  if (!saved || saved.email !== data.email || saved.password !== data.password) {
    document.querySelector('#loginError').textContent = 'Email or password is incorrect.';
    return;
  }
  localStorage.setItem(sessionKey, 'true');
  window.location.href = '/dashboard';
});

const userName = document.querySelector('#userName');
if (userName && localStorage.getItem(sessionKey) !== 'true') window.location.href = '/login';
if (userName) userName.textContent = (getUser()?.name || 'there').split(' ')[0];

if (userName) {
  document.querySelectorAll('a[href="/"]').forEach((link) => {
    const label = link.textContent.trim().toLowerCase();
    if (label.includes('predict') || label.includes('screening')) link.href = '/predict';
  });
}

const historyRows = document.querySelector('#historyRows');
if (historyRows) {
  const scopedHistoryKey = getHistoryKey();
  const history = JSON.parse(localStorage.getItem(scopedHistoryKey) || '[]');
  document.querySelector('#screeningCount').textContent = history.length;
  if (history.length) {
    const latest = history[0];
    document.querySelector('#latestDisease').textContent = latest.disease;
    document.querySelector('#latestDate').textContent = latest.date;
    historyRows.innerHTML = history.map(item => `<div class="history-row"><span>${item.date}</span><strong>${item.disease}</strong><span>${item.probability}%</span><b class="status ${item.risk}">${item.risk === 'higher' ? 'Review' : 'Lower signal'}</b></div>`).join('');
  }
}

document.querySelector('#logoutLink')?.addEventListener('click', (event) => { event.preventDefault(); localStorage.removeItem(sessionKey); window.location.href = '/login'; });

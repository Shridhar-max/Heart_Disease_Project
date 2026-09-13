const userKey = 'heartpredict_user';
const sessionKey = 'heartpredict_session';
const historyKey = 'heartpredict_history';
const noticeKey = 'heartpredict_auth_notice';
const readStoredJson = (key, fallback) => {
  try {
    const value = localStorage.getItem(key);
    return value ? JSON.parse(value) : fallback;
  } catch (error) {
    localStorage.removeItem(key);
    return fallback;
  }
};
const getUser = () => readStoredJson(userKey, null);
const getHistoryKey = () => `${historyKey}_${encodeURIComponent(getUser()?.email || 'guest')}`;

const validatePassword = (password) => {
  const checks = [
    password.length >= 8,
    /[a-z]/.test(password),
    /[A-Z]/.test(password),
    /\d/.test(password),
    /[^A-Za-z0-9]/.test(password)
  ];
  return checks.every(Boolean);
};

const updatePasswordRules = (password) => {
  const rules = document.querySelectorAll('.password-rule');
  const checks = [
    password.length >= 8,
    /[a-z]/.test(password),
    /[A-Z]/.test(password),
    /\d/.test(password),
    /[^A-Za-z0-9]/.test(password)
  ];

  rules.forEach((rule, index) => {
    const isValid = checks[index];
    rule.classList.toggle('valid', isValid);
    rule.textContent = index === 0 ? '8+ characters' : index === 1 ? 'Lowercase' : index === 2 ? 'Uppercase' : index === 3 ? 'Number' : 'Symbol';
  });
};

const passwordInput = document.querySelector('#passwordInput');
if (passwordInput) {
  passwordInput.addEventListener('input', (event) => {
    updatePasswordRules(event.target.value);
  });
}

const registerForm = document.querySelector('#registerForm');
if (registerForm) registerForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(registerForm).entries());
  const passwordError = document.querySelector('#registerError');
  const existing = getUser();

  if (!validatePassword(data.password)) {
    passwordError.textContent = 'Password must be at least 8 characters and include uppercase, lowercase, a number, and a symbol.';
    return;
  }

  if (existing?.email === data.email) {
    passwordError.textContent = 'An account with this email already exists. Please login.';
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
  const history = readStoredJson(scopedHistoryKey, []);
  document.querySelector('#screeningCount').textContent = history.length;
  if (history.length) {
    const latest = history[0];
    document.querySelector('#latestDisease').textContent = latest.disease;
    document.querySelector('#latestDate').textContent = latest.date;
    historyRows.innerHTML = history.map(item => `<div class="history-row"><span>${item.date}</span><strong>${item.disease}</strong><span>${item.probability}%</span><b class="status ${item.risk}">${item.risk === 'higher' ? 'Review' : 'Lower signal'}</b></div>`).join('');
  }
}

document.querySelector('#logoutLink')?.addEventListener('click', (event) => { event.preventDefault(); localStorage.removeItem(sessionKey); window.location.href = '/login'; });

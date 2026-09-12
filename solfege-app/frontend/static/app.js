const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const uploader = document.getElementById('uploader');
const statusSection = document.getElementById('status');
const statusText = document.getElementById('statusText');
const errorBox = document.getElementById('errorBox');
const errorText = document.getElementById('errorText');
const retryBtn = document.getElementById('retryBtn');
const resultsSection = document.getElementById('results');
const newBtn = document.getElementById('newBtn');
const keyPill = document.getElementById('keyPill');
const staffStrip = document.getElementById('staffStrip');

const STATUS_MESSAGES = [
  'Reading the staff…',
  'Finding the key signature…',
  'Naming each note…',
  'Turning pitches into Do-Re-Mi…'
];

function showOnly(section) {
  [uploader, statusSection, errorBox, resultsSection].forEach(s => s.hidden = true);
  section.hidden = false;
}

browseBtn.addEventListener('click', () => fileInput.click());
dropzone.addEventListener('click', () => fileInput.click());

dropzone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropzone.classList.add('drag-over');
});
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
dropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropzone.classList.remove('drag-over');
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});

fileInput.addEventListener('change', () => {
  if (fileInput.files.length) handleFile(fileInput.files[0]);
});

retryBtn.addEventListener('click', () => {
  fileInput.value = '';
  showOnly(uploader);
});

newBtn.addEventListener('click', () => {
  fileInput.value = '';
  showOnly(uploader);
});

let statusInterval;

function cycleStatusMessages() {
  let i = 0;
  statusText.textContent = STATUS_MESSAGES[0];
  statusInterval = setInterval(() => {
    i = (i + 1) % STATUS_MESSAGES.length;
    statusText.textContent = STATUS_MESSAGES[i];
  }, 2200);
}

async function handleFile(file) {
  showOnly(statusSection);
  cycleStatusMessages();

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/api/convert', { method: 'POST', body: formData });
    const data = await res.json();
    clearInterval(statusInterval);

    if (!res.ok || !data.success) {
      throw new Error(data.detail || data.error || 'Could not read that image.');
    }
    renderResults(data);
  } catch (err) {
    clearInterval(statusInterval);
    errorText.textContent = err.message || 'Something went wrong reading the score.';
    showOnly(errorBox);
  }
}

const CHROMATIC_SET = new Set(['Di','Ra','Ri','Me','Fi','Se','Si','Le','Li','Te']);

function renderResults(data) {
  keyPill.textContent = data.key;
  staffStrip.innerHTML = '';

  data.measures.forEach(measure => {
    if (!measure.notes.length) return;
    const row = document.createElement('div');
    row.className = 'measure-row';

    const num = document.createElement('span');
    num.className = 'measure-num';
    num.textContent = measure.measure_number ?? '';
    row.appendChild(num);

    measure.notes.forEach(n => {
      if (n.type === 'rest') {
        const r = document.createElement('span');
        r.className = 'rest-mark';
        r.textContent = '𝄽';
        row.appendChild(r);
      } else {
        const s = document.createElement('span');
        s.className = 'syllable' + (CHROMATIC_SET.has(n.syllable) ? ' chromatic' : '');
        s.textContent = n.syllable;
        s.title = n.letter;
        row.appendChild(s);
      }
    });

    staffStrip.appendChild(row);
  });

  showOnly(resultsSection);
}

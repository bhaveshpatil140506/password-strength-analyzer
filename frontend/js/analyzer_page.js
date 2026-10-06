/* ============================================================
   PASSWORD STRENGTH ANALYZER - ANALYZER PAGE CONTROLLER
   ============================================================ */

const PSA_AnalyzerPage = {

  run() {
    const input = document.getElementById('password');
    if (!input) return;
    const pw = input.value;

    if (!pw) {
      PSA.toast('Enter a password to analyze', 'error');
      return;
    }
    PSA.toast('Running deep analysis...', 'info');

    PSA_AnalyzerPage.toggleLoading(true);
    PSA_Analyzer.analyze(pw).then(result => {
      window.PREV_RESULT = result;
      PSA_Analyzer.renderResult(result, 'analysis-result');
      PSA_AnalyzerPage.toggleLoading(false);
    }).catch(() => {
      PSA_AnalyzerPage.toggleLoading(false);
      PSA.toast('Analysis failed. Try again.', 'error');
    });
  },

  clearResult() {
    const box = document.getElementById('analysis-result');
    if (box) { box.classList.remove('show'); box.innerHTML = ''; }
    window.PREV_RESULT = null;
  },

  toggleLoading(on) {
    const box = document.getElementById('analysis-result');
    if (!box) return;
    if (on) {
      box.classList.add('show');
      box.innerHTML = '<div class="loading show"><div class="typing-indicator">ANALYZING ENTROPY <span>.</span><span>.</span><span>.</span></div></div>';
    }
  },

  bind() {
    PSA_Validator.bindStrengthMeter('password', 'password-meter', 'password-label', 'password-criteria');
    document.getElementById('password').addEventListener('keydown', e => {
      if (e.key === 'Enter') { e.preventDefault(); PSA_AnalyzerPage.run(); }
    });
  }
};

document.addEventListener('DOMContentLoaded', () => PSA_AnalyzerPage.bind());

(() => {
  const landing = document.getElementById('landing-view');
  if (!landing) return;

  const scenes = [...landing.querySelectorAll('[data-ark-scene]')];
  const navigation = [...landing.querySelectorAll('[data-ark-go]')];
  const pageNumber = document.getElementById('ark-page-number');
  const scrollCue = landing.querySelector('.ark-scroll-cue small');
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const state = { current: 0, session: null, visible: false, entering: false };
  let transitionLocked = false;
  let wheelTotal = 0;
  let wheelGestureUsed = false;
  let wheelResetTimer;
  let touchStartY = null;

  function setScene(index, announce = true) {
    const next = Math.max(0, Math.min(scenes.length - 1, index));
    if (next === state.current && announce) return;
    const previous = state.current;
    state.current = next;
    scenes.forEach((scene, sceneIndex) => {
      scene.classList.toggle('is-active', sceneIndex === next);
      scene.classList.toggle('is-before', sceneIndex < next);
      scene.classList.toggle('is-after', sceneIndex > next);
      scene.setAttribute('aria-hidden', String(sceneIndex !== next));
    });
    navigation.forEach((button, buttonIndex) => {
      const active = buttonIndex === next;
      button.classList.toggle('active', active);
      if (active) button.setAttribute('aria-current', 'step');
      else button.removeAttribute('aria-current');
    });
    pageNumber.textContent = String(next + 1).padStart(2, '0');
    scrollCue.textContent = next === scenes.length - 1 ? 'SYSTEM READY' : next > previous ? 'CONTINUE TO REVEAL' : 'SCROLL TO REVEAL';
  }

  function goTo(index) {
    if (!state.visible || state.entering || transitionLocked || index === state.current) return;
    transitionLocked = true;
    setScene(index);
    window.setTimeout(() => { transitionLocked = false; }, reducedMotion ? 150 : 960);
  }

  function step(direction) { goTo(state.current + direction); }

  function onWheel(event) {
    if (!state.visible || state.entering) return;
    event.preventDefault();
    clearTimeout(wheelResetTimer);
    wheelResetTimer = window.setTimeout(() => {
      wheelTotal = 0;
      wheelGestureUsed = false;
    }, 190);
    if (wheelGestureUsed || transitionLocked) return;
    wheelTotal += event.deltaY;
    if (Math.abs(wheelTotal) < 58) return;
    wheelGestureUsed = true;
    step(wheelTotal > 0 ? 1 : -1);
  }

  function onKeydown(event) {
    if (!state.visible || state.entering || event.altKey || event.ctrlKey || event.metaKey) return;
    const forward = ['ArrowDown', 'PageDown', ' '];
    const backward = ['ArrowUp', 'PageUp'];
    if (forward.includes(event.key)) { event.preventDefault(); step(1); }
    else if (backward.includes(event.key)) { event.preventDefault(); step(-1); }
    else if (event.key === 'Home') { event.preventDefault(); goTo(0); }
    else if (event.key === 'End') { event.preventDefault(); goTo(scenes.length - 1); }
  }

  function onTouchStart(event) { touchStartY = event.changedTouches[0]?.clientY ?? null; }
  function onTouchEnd(event) {
    if (touchStartY === null || !state.visible || state.entering) return;
    const distance = touchStartY - (event.changedTouches[0]?.clientY ?? touchStartY);
    touchStartY = null;
    if (Math.abs(distance) > 46) step(distance > 0 ? 1 : -1);
  }

  function requestEntry() {
    if (!state.visible || state.entering) return;
    state.entering = true;
    landing.classList.add('is-entering');
    window.dispatchEvent(new CustomEvent('ark:enter-workbench', { detail: { session: state.session } }));
  }

  async function loadRuntimeStatus() {
    const bootStatus = document.getElementById('boot-status');
    try {
      const response = await fetch('/api/health', { credentials: 'same-origin' });
      if (!response.ok) throw new Error('Health unavailable');
      const health = await response.json();
      const models = health.model_status || [];
      const installed = models.filter(model => model.status === 'installed').length;
      document.getElementById('ark-model-status').textContent = `${installed} of ${models.length} local models installed`;
      document.getElementById('ark-runtime-status').textContent = health.database === 'connected' ? 'LOCAL SERVICE READY' : 'LOCAL SERVICE AVAILABLE';
      document.getElementById('ark-runtime-detail').textContent = `${health.milestone || 'Local runtime'} · ${installed} model routes installed`;
      bootStatus.textContent = health.database === 'connected' ? 'Local runtime ready' : 'Local interface ready';
    } catch {
      document.getElementById('ark-model-status').textContent = 'Model status available inside the workbench';
      document.getElementById('ark-runtime-status').textContent = 'LOCAL STATUS UNAVAILABLE';
      document.getElementById('ark-runtime-detail').textContent = 'Open the workbench to retry the local service check.';
      bootStatus.textContent = 'Local interface ready';
    }
  }

  async function updateSession(session) {
    state.session = session || null;
    const copy = document.getElementById('ark-session-copy');
    const buttonLabel = document.querySelector('#ark-enter-final span');
    if (!session?.user) {
      copy.textContent = 'Continue to secure local access.';
      buttonLabel.textContent = 'ENTER ARK';
      return;
    }
    buttonLabel.textContent = 'OPEN MY WORKBENCH';
    copy.textContent = `Local session ready for ${session.user.display_name}.`;
    try {
      const response = await fetch('/api/workspaces', { credentials: 'same-origin' });
      if (!response.ok) return;
      const data = await response.json();
      copy.textContent = `Local session ready for ${session.user.display_name} · ${data.workspaces.length} workspace${data.workspaces.length === 1 ? '' : 's'} available.`;
    } catch { /* The authenticated workbench will retry. */ }
  }

  async function show(session) {
    state.visible = true;
    state.entering = false;
    landing.classList.remove('is-entering');
    landing.hidden = false;
    document.body.classList.add('ark-landing-open');
    setScene(0, false);
    const minimumIntro = new Promise(resolve => window.setTimeout(resolve, reducedMotion ? 120 : 1050));
    await Promise.all([loadRuntimeStatus(), updateSession(session), minimumIntro]);
    const boot = document.getElementById('boot');
    boot.classList.add('is-leaving');
    window.setTimeout(() => { boot.hidden = true; }, reducedMotion ? 130 : 560);
  }

  function hide(immediate = false) {
    state.visible = false;
    document.body.classList.remove('ark-landing-open');
    const finish = () => {
      landing.hidden = true;
      landing.classList.remove('is-entering');
      state.entering = false;
    };
    if (immediate || reducedMotion) finish();
    else window.setTimeout(finish, 580);
  }

  navigation.forEach(button => button.addEventListener('click', () => goTo(Number(button.dataset.arkGo))));
  landing.querySelector('.ark-wordmark').addEventListener('click', event => { event.preventDefault(); goTo(0); });
  document.getElementById('ark-enter-header').addEventListener('click', requestEntry);
  document.getElementById('ark-enter-final').addEventListener('click', requestEntry);
  window.addEventListener('wheel', onWheel, { passive: false });
  window.addEventListener('keydown', onKeydown);
  landing.addEventListener('touchstart', onTouchStart, { passive: true });
  landing.addEventListener('touchend', onTouchEnd, { passive: true });

  window.ARKLanding = { show, hide, updateSession, get session() { return state.session; } };
})();

(() => {
  const tabs = [...document.querySelectorAll('[role="tab"][data-case]')];
  const panels = [...document.querySelectorAll('.case-panel')];
  const tablist = document.querySelector('.case-tabs');
  const select = (id, updateUrl = false) => {
    const active = tabs.find(tab => tab.dataset.case === id);
    if (!active) return;
    tabs.forEach(tab => {
      const selected = tab === active;
      tab.setAttribute('aria-selected', String(selected));
      tab.tabIndex = selected ? 0 : -1;
    });
    panels.forEach(panel => { panel.hidden = panel.id !== `case-${id}`; });
    if (updateUrl) history.replaceState(null, '', `#case-${id}`);
  };
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => select(tab.dataset.case, true));
    tab.addEventListener('keydown', event => {
      let next;
      if (['ArrowRight', 'ArrowDown'].includes(event.key)) next = (index + 1) % tabs.length;
      if (['ArrowLeft', 'ArrowUp'].includes(event.key)) next = (index - 1 + tabs.length) % tabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      if (next === undefined) return;
      event.preventDefault();
      select(tabs[next].dataset.case, true);
      tabs[next].focus();
    });
  });
  const fromHash = () => {
    if (location.hash.startsWith('#case-')) select(location.hash.slice(6));
  };
  fromHash();
  addEventListener('hashchange', fromHash);
  const horizontal = matchMedia('(max-width: 800px)');
  const orientation = () => tablist?.setAttribute('aria-orientation', horizontal.matches ? 'horizontal' : 'vertical');
  orientation();
  horizontal.addEventListener('change', orientation);
  document.querySelectorAll('[data-view]').forEach(button => {
    button.addEventListener('click', () => {
      const visual = button.closest('.case-visual');
      visual.querySelector('.road-visual').dataset.view = button.dataset.view;
      visual.querySelectorAll('[data-view]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    });
  });
  // A projective map between the drawn image trapezoid and a unit ground plane.
  // Coordinates are dimensionless: this is geometry, not a calibrated measurement.
  const road = document.querySelector('.road-visual');
  if (road) {
    const quad = [[313, 63], [438, 63], [656, 302], [110, 302]];
    const unit = [[0, 0], [1, 0], [1, 1], [0, 1]];
    function homography(from, to) {
      const rows = [];
      from.forEach(([x, y], i) => {
        const [u, v] = to[i];
        rows.push([x, y, 1, 0, 0, 0, -u*x, -u*y, u]);
        rows.push([0, 0, 0, x, y, 1, -v*x, -v*y, v]);
      });
      for (let column = 0; column < 8; column++) {
        let pivot = column;
        for (let i = column + 1; i < 8; i++) if (Math.abs(rows[i][column]) > Math.abs(rows[pivot][column])) pivot = i;
        [rows[column], rows[pivot]] = [rows[pivot], rows[column]];
        const divisor = rows[column][column];
        rows[column] = rows[column].map(value => value / divisor);
        for (let i = 0; i < 8; i++) {
          if (i === column) continue;
          const factor = rows[i][column];
          rows[i] = rows[i].map((value, j) => value - factor * rows[column][j]);
        }
      }
      const h = rows.map(row => row[8]);
      return (x, y) => {
        const scale = h[6]*x + h[7]*y + 1;
        return [(h[0]*x + h[1]*y + h[2])/scale, (h[3]*x + h[4]*y + h[5])/scale];
      };
    }
    const toImage = homography(unit, quad);
    const toGround = homography(quad, unit);
    let x = .45, y = .55;
    const controls = document.querySelector('.projection-controls');
    const renderPoint = () => {
      const image = toImage(x, y);
      const point = road.dataset.view === 'ground' ? [230 + x*290, 35 + y*277] : image;
      road.querySelector('.projection-marker').setAttribute('transform', `translate(${point[0]} ${point[1]})`);
      controls.querySelector('output').textContent = `u,v ${Math.round(image[0])},${Math.round(image[1])} → x,y ${x.toFixed(2)},${y.toFixed(2)}`;
      controls.querySelector('[data-axis=x]').value = Math.round(x*100);
      controls.querySelector('[data-axis=y]').value = Math.round(y*100);
    };
    controls.querySelectorAll('input').forEach(input => input.addEventListener('input', () => {
      if (input.dataset.axis === 'x') x = Number(input.value)/100;
      else y = Number(input.value)/100;
      renderPoint();
    }));
    const placePoint = event => {
      const matrix = road.getScreenCTM();
      if (!matrix) return;
      const point = new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse());
      const ground = road.dataset.view === 'ground' ? [(point.x-230)/290, (point.y-35)/277] : toGround(point.x, point.y);
      if (!ground.every(Number.isFinite) || ground.some(value => value < 0 || value > 1)) return;
      [x, y] = ground;
      renderPoint();
    };
    road.addEventListener('pointerdown', event => { placePoint(event); });
    road.addEventListener('pointermove', event => { if (event.buttons === 1) placePoint(event); });
    document.querySelectorAll('.view-control button').forEach(button => button.addEventListener('click', renderPoint));
    renderPoint();
  }
  const copy = document.querySelector('[data-copy-email]');
  copy?.addEventListener('click', async () => {
    const status = document.querySelector('.copy-status');
    try {
      await navigator.clipboard.writeText(copy.dataset.email);
      status.textContent = copy.dataset.success;
    } catch {
      status.textContent = copy.dataset.failure;
    }
  });
  document.querySelector('[data-print]')?.addEventListener('click', () => window.print());
  let previousDetails = [];
  addEventListener('beforeprint', () => {
    previousDetails = [...document.querySelectorAll('.job details')].map(item => [item, item.open]);
    previousDetails.forEach(([item]) => { item.open = true; });
  });
  addEventListener('afterprint', () => previousDetails.forEach(([item, open]) => { item.open = open; }));
  document.documentElement.classList.add('js');
})();

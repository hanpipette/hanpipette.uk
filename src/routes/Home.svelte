<script lang="ts">
  import { push } from 'svelte-spa-router';

  // ── State ─────────────────────────────────────
  let mx = $state(0);
  let my = $state(0);
  let rawX = $state(0);
  let rawY = $state(0);
  let cursorVisible = $state(false);
  let mounted = $state(false);
  let overloaded = $state(false);
  let titleHover = $state(false);
  let title = $state('ふゆ');
  let clicks: Array<{ id: number; x: number; y: number }> = $state([]);
  let clickCount = $state(0);
  let activeModal: string | null = $state(null);

  // ── Constants ─────────────────────────────────
  const GLITCH = 'アイウエオカキクケコサシスセソタチツテト!@#$%&*<>01';

  const PARTICLES = Array.from({ length: 28 }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: Math.random() * 5 + 3,
    delay: Math.random() * 12,
    duration: Math.random() * 10 + 8,
    symbol: ['✦', '·', '×', '+', '⊹', '○', '◇', '•'][Math.floor(Math.random() * 8)],
    px: (Math.random() - 0.5) * 30,
  }));

  // ── Mouse / touch / click ─────────────────────
  $effect(() => {
    const t = setTimeout(() => (mounted = true), 150);

    const onMove = (e: MouseEvent) => {
      cursorVisible = true;
      rawX = e.clientX;
      rawY = e.clientY;
      mx = (e.clientX / window.innerWidth - 0.5) * 2;
      my = (e.clientY / window.innerHeight - 0.5) * 2;
    };

    const onTouch = (e: TouchEvent) => {
      const t = e.touches[0];
      mx = (t.clientX / window.innerWidth - 0.5) * 2;
      my = (t.clientY / window.innerHeight - 0.5) * 2;
    };

    const onClick = (e: MouseEvent) => {
      const id = performance.now();
      clicks = [...clicks, { id, x: e.clientX, y: e.clientY }];
      setTimeout(() => { clicks = clicks.filter((c) => c.id !== id); }, 700);

      clickCount++;
      setTimeout(() => clickCount--, 2000);
      if (clickCount >= 4 && !overloaded) {
        overloaded = true;
        setTimeout(() => (overloaded = false), 1800);
      }
    };

    window.addEventListener('mousemove', onMove, { passive: true });
    window.addEventListener('touchmove', onTouch, { passive: true });
    window.addEventListener('click', onClick);

    return () => {
      clearTimeout(t);
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('touchmove', onTouch);
      window.removeEventListener('click', onClick);
    };
  });

  // ── Title scramble ────────────────────────────
  let scrambleTimer: ReturnType<typeof setInterval> | null = null;

  function onTitleEnter() {
    titleHover = true;
    if (scrambleTimer) clearInterval(scrambleTimer);
    let iter = 0;
    scrambleTimer = setInterval(() => {
      title = 'ふゆ'
        .split('')
        .map((_, i) =>
          i < Math.floor(iter) ? 'ふゆ'[i] : GLITCH[Math.floor(Math.random() * GLITCH.length)],
        )
        .join('');
      iter += 0.35;
      if (iter >= 3) {
        if (scrambleTimer) clearInterval(scrambleTimer);
        scrambleTimer = null;
        title = 'ふゆ';
      }
    }, 30);
  }

  function onTitleLeave() {
    titleHover = false;
    if (scrambleTimer) {
      clearInterval(scrambleTimer);
      scrambleTimer = null;
    }
    title = 'ふゆ';
  }

  function onTitleTouch() {
    onTitleLeave();
    requestAnimationFrame(onTitleEnter);
  }
</script>

<svelte:head>
  <title>ふゆ — 電脳随筆</title>
  <meta name="description" content="Han Winter — 地雷系でごめんね" />
</svelte:head>

<main class="page" class:mounted class:overloaded style="--mx:{mx};--my:{my}">
  <!-- Cursor glow -->
  <div
    class="cursor-glow"
    class:visible={cursorVisible}
    style="transform:translate3d({rawX}px,{rawY}px,0)"
    aria-hidden="true"
  ></div>

  <!-- Click bursts -->
  {#each clicks as click (click.id)}
    <div
      class="click-ring"
      style="left:{click.x}px;top:{click.y}px"
      aria-hidden="true"
    ></div>
  {/each}

  <!-- Overload flash -->
  {#if overloaded}
    <div class="overload-flash" aria-hidden="true"></div>
  {/if}

  <!-- ── Tickers ── -->
  <div class="ticker ticker-top" aria-hidden="true">
    <div class="ticker-track">
      <span>接続過多 /// SIGNAL_LOST /// 返信まだかな /// overflow: hidden /// 404 愛が見つかりません /// 好きって言って /// rm -rf feelings /// 地雷系 /// NULL /// ﾒﾝﾍﾗ製造機 /// 今消えたい ///&nbsp;</span>
      <span>接続過多 /// SIGNAL_LOST /// 返信まだかな /// overflow: hidden /// 404 愛が見つかりません /// 好きって言って /// rm -rf feelings /// 地雷系 /// NULL /// ﾒﾝﾍﾗ製造機 /// 今消えたい ///&nbsp;</span>
    </div>
  </div>
  <div class="ticker ticker-bottom" aria-hidden="true">
    <div class="ticker-track ticker-reverse">
      <span>病みかわ /// DISCONNECTED /// 平気なふりしてる /// segfault /// ﾒﾝﾍﾗ /// 0xFF00FF /// 執着してごめん /// 愛されたい.sh /// 地雷女 /// fatal error /// 束縛していい？ ///&nbsp;</span>
      <span>病みかわ /// DISCONNECTED /// 平気なふりしてる /// segfault /// ﾒﾝﾍﾗ /// 0xFF00FF /// 執着してごめん /// 愛されたい.sh /// 地雷女 /// fatal error /// 束縛していい？ ///&nbsp;</span>
    </div>
  </div>

  <!-- ── Side scrolls ── -->
  <div class="side-scroll side-left" aria-hidden="true">
    <div class="side-track">
      <span>地雷系 地雷系 地雷系 地雷系 地雷系 地雷系 地雷系 地雷系&nbsp;</span>
      <span>地雷系 地雷系 地雷系 地雷系 地雷系 地雷系 地雷系 地雷系&nbsp;</span>
    </div>
  </div>
  <div class="side-scroll side-right" aria-hidden="true">
    <div class="side-track side-track-reverse">
      <span>MENHERA MENHERA MENHERA MENHERA MENHERA MENHERA MENHERA MENHERA&nbsp;</span>
      <span>MENHERA MENHERA MENHERA MENHERA MENHERA MENHERA MENHERA MENHERA&nbsp;</span>
    </div>
  </div>

  <!-- ── Particles ── -->
  <div class="particles" aria-hidden="true">
    {#each PARTICLES as p (p.id)}
      <span
        class="particle"
        style="left:{p.x}%;top:{p.y}%;font-size:{p.size}px;--pd:{p.delay}s;--pdur:{p.duration}s;--ppx:{p.px}"
      >{p.symbol}</span>
    {/each}
  </div>

  <!-- ── Windows ── -->
  <div class="window window-1" aria-hidden="true">
    <div class="window-bar">
      <span class="window-title">error.sh</span>
      <div class="window-btns"><span class="wbtn">─</span><span class="wbtn">□</span><span class="wbtn wbtn-x">×</span></div>
    </div>
    <div class="window-body">
      <p>⚠ 感情の処理に失敗しました</p>
      <p class="win-sub">libemotion.so not found</p>
      <div class="win-row">
        <button class="win-action" tabindex="-1">OK</button>
        <button class="win-action" tabindex="-1">見なかったことにする</button>
      </div>
    </div>
  </div>

  <div class="window window-2" aria-hidden="true">
    <div class="window-bar">
      <span class="window-title">/proc/heartbeat</span>
      <div class="window-btns"><span class="wbtn">─</span><span class="wbtn">□</span><span class="wbtn wbtn-x">×</span></div>
    </div>
    <div class="window-body body-dark">
      <p class="heartbeat">♡ ♡ ♡ ♡</p>
      <p class="win-sub">STATUS: <span class="txt-red">不安定</span></p>
    </div>
  </div>

  <div class="window window-3" aria-hidden="true">
    <div class="window-bar">
      <span class="window-title">~/.diary</span>
      <div class="window-btns"><span class="wbtn">─</span><span class="wbtn">□</span><span class="wbtn wbtn-x">×</span></div>
    </div>
    <div class="window-body body-dark">
      <p class="diary">全部消したのに<br />まだ通知音が聞こえる<br />既読つけたくせに<br />なんで何も言わないの</p>
    </div>
  </div>

  <div class="window window-4" aria-hidden="true">
    <div class="window-bar">
      <span class="window-title">/var/log/menhera</span>
      <div class="window-btns"><span class="wbtn">─</span><span class="wbtn">□</span><span class="wbtn wbtn-x">×</span></div>
    </div>
    <div class="window-body body-dark log-body">
      <p>> scanning emotions...</p>
      <p>> <span class="txt-red">CRITICAL:</span> 依存度 99.9%</p>
      <p>> <span class="txt-warn">WARN:</span> 48時間の睡眠不足</p>
      <p>> <span class="txt-red">FATAL:</span> 自己肯定感 = 0</p>
      <p>&gt; 応答なし...<button
        type="button"
        class="cursor-blink secret-entry"
        onclick={(e) => { e.stopPropagation(); push('/chat'); }}
        aria-label="secret"
      >▊</button></p>
    </div>
  </div>

  <!-- ── Floating text ── -->
  <div class="floaters" aria-hidden="true">
    <span class="fl fl-1" style="--fp:8">✦</span>
    <span class="fl fl-2" style="--fp:18">×</span>
    <span class="fl fl-3" style="--fp:5">(；ω；)</span>
    <span class="fl fl-4" style="--fp:14">▸▸▸</span>
    <span class="fl fl-5" style="--fp:22">♱</span>
    <span class="fl fl-6" style="--fp:6">既読無視</span>
    <span class="fl fl-7" style="--fp:16">💊</span>
    <span class="fl fl-8" style="--fp:10">ERR</span>
    <span class="fl fl-9" style="--fp:20">♡̸</span>
    <span class="fl fl-10" style="--fp:7">⚠</span>
    <span class="fl fl-11" style="--fp:12">;;;</span>
    <span class="fl fl-12" style="--fp:25">かまって</span>
    <span class="fl fl-13" style="--fp:9">NULL</span>
    <span class="fl fl-14" style="--fp:15">†</span>
    <span class="fl fl-15" style="--fp:11">⌫</span>
  </div>

  <!-- ── Main frame ── -->
  <div class="frame">
    <span class="corner c-tl" aria-hidden="true">+</span>
    <span class="corner c-tr" aria-hidden="true">+</span>
    <span class="corner c-bl" aria-hidden="true">+</span>
    <span class="corner c-br" aria-hidden="true">+</span>

    <div class="meta-bar" aria-hidden="true">
      <p>han winter</p>
      <p>病みかわ電脳随筆</p>
    </div>

    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
      class="centerpiece"
      onmouseenter={onTitleEnter}
      onmouseleave={onTitleLeave}
      ontouchstart={onTitleTouch}
    >
      <div class="ghost ghost-a" aria-hidden="true">
        <span>ふゆ</span>
      </div>
      <div class="ghost ghost-b" aria-hidden="true">
        <span>ふゆ</span>
      </div>

      <h1 class:title-hover={titleHover}>
        <span data-text={title}>{title}</span>
      </h1>

      <p class="tagline">地雷系でごめんね</p>

      <nav class="links">
        <button class="pill" onclick={() => activeModal = 'signal'}>SIGNAL</button>
        <button class="pill" onclick={() => activeModal = 'archive'}>ARCHIVE</button>
        <button class="pill" onclick={() => activeModal = 'void'}>VOID</button>
      </nav>
    </div>

    <div class="bottom-bar" aria-hidden="true">
      <p>SYS.STATUS: <span class="blink-red">情緒不安定</span></p>
      <p>2026 — 電脳随筆</p>
    </div>
  </div>

  <!-- ── Modal ── -->
  {#if activeModal}
    <!-- svelte-ignore a11y_no_static_element_interactions a11y_click_events_have_key_events a11y_interactive_supports_focus -->
    <div class="modal-backdrop" onclick={() => activeModal = null} role="dialog" aria-modal="true" tabindex="-1">
      <!-- svelte-ignore a11y_no_static_element_interactions a11y_click_events_have_key_events -->
      <div class="modal" onclick={(e) => e.stopPropagation()}>
        <div class="modal-bar">
          <span class="window-title">{activeModal === 'signal' ? '> playlist — 感情汚染' : activeModal === 'archive' ? '> cat ~/.diary' : '> /dev/null'}</span>
          <button class="modal-close" onclick={() => activeModal = null}>×</button>
        </div>
        <div class="modal-body">

          {#if activeModal === 'signal'}
            <h2 class="modal-title">SIGNAL</h2>
            <div class="playlist">
              <a class="track" href="https://www.youtube.com/watch?v=vCEnbvwSGQc" target="_blank" rel="noopener">
                <span class="track-num">01</span>
                <div>
                  <p class="track-name">なんとかしてよ</p>
                  <p class="track-artist">重音テトSV & ナースロボ＿タイプT</p>
                </div>
              </a>
              <a class="track" href="https://www.youtube.com/watch?v=4QXCPuwBz2E" target="_blank" rel="noopener">
                <span class="track-num">02</span>
                <div>
                  <p class="track-name">あの世行きのバスに乗ってさらば。</p>
                  <p class="track-artist">ツユ</p>
                </div>
              </a>
              <a class="track" href="https://www.youtube.com/watch?v=UnIhRpIT7nc" target="_blank" rel="noopener">
                <span class="track-num">03</span>
                <div>
                  <p class="track-name">ラグトレイン</p>
                  <p class="track-artist">稲葉曇</p>
                </div>
              </a>
              <a class="track" href="https://www.youtube.com/watch?v=hc0ZDaAZQT0" target="_blank" rel="noopener">
                <span class="track-num">04</span>
                <div>
                  <p class="track-name">るるちゃんの自殺配信</p>
                  <p class="track-artist">神聖かまってちゃん</p>
                </div>
              </a>
              <a class="track" href="https://www.youtube.com/watch?v=H08YWE4CIFQ" target="_blank" rel="noopener">
                <span class="track-num">05</span>
                <div>
                  <p class="track-name">Overdose</p>
                  <p class="track-artist">なとり</p>
                </div>
              </a>
            </div>

          {:else if activeModal === 'archive'}
            <h2 class="modal-title">ARCHIVE</h2>
            <div class="diary-entries">
              <article class="entry">
                <time>2026.03.28 — 03:42</time>
                <p>또 이 시간이다. 알림이 없는 게 무섭다.<br />화면 빛만이 친구 같아.</p>
              </article>
              <article class="entry">
                <time>2026.03.15 — 23:17</time>
                <p>전부 지웠다. 사진도, 메시지도.<br />그런데 기억은 못 지우겠다.</p>
              </article>
              <article class="entry">
                <time>2026.02.28 — 04:55</time>
                <p>괜찮은 척이 늘었다.<br />근데 밤은 아직 서툴러.</p>
              </article>
            </div>

          {:else if activeModal === 'void'}
            <h2 class="modal-title">VOID</h2>
            <div class="void-content">
              <p>> initiating shutdown...</p>
              <p>> saving unsaved emotions... <span class="txt-red">failed</span></p>
              <p>> closing connections... 0 remaining</p>
              <p class="void-spacer"></p>
              <p class="void-poem">아무것도 없는 곳이</p>
              <p class="void-poem">제일 편해</p>
              <p class="void-spacer"></p>
              <p>> <span class="txt-red">[system halted]</span></p>
            </div>
          {/if}

        </div>
      </div>
    </div>
  {/if}

  <!-- ── Overlays ── -->
  <div class="scanlines" aria-hidden="true"></div>
  <div class="noise" aria-hidden="true"></div>
  <div class="vignette" aria-hidden="true"></div>
</main>

<script>
  let activeTab = $state('problem');
  let zoom = $state(100);
  let activePhase = $state('design');

  const phases = [
    { id: 'clarify', label: 'Clarify', icon: '💬' },
    { id: 'estimate', label: 'Estimate', icon: '🧮' },
    { id: 'design', label: 'Design', icon: '⚡' },
    { id: 'explain', label: 'Explain', icon: '🎙️' },
  ];

  const tools = [
    { icon: '↖', label: 'Select' },
    { icon: '□', label: 'Rectangle', active: true },
    { icon: '◇', label: 'Diamond' },
    { icon: '○', label: 'Circle' },
    { icon: '→', label: 'Arrow' },
    { icon: '✏', label: 'Draw' },
    { icon: 'T', label: 'Text' },
  ];

  const functionalReqs = [
    'Given a long URL, return a unique short URL.',
    'When clicking the short URL, redirect to the original URL.',
    'Links should expire after a standard default timespan.',
    'Users should be able to specify a custom alias.',
  ];

  const nonFunctionalReqs = [
    'System must be highly available.',
    'URL redirection should happen in real-time with minimal latency.',
    'Shortened links should not be guessable (predictable).',
  ];
</script>

<svelte:head>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Inter:wght@300;400;500;600&family=Caveat:wght@400;700&display=swap" rel="stylesheet" />
</svelte:head>

<div class="h-screen flex flex-col bg-base-300 text-base-content font-sans overflow-hidden" style="font-family: 'Inter', sans-serif;">
  <!-- Navbar -->
  <div class="navbar bg-base-100 border-b border-base-300 shadow-md px-4 h-16 shrink-0 z-10">
    <div class="navbar-start">
      <span class="text-2xl animate-pulse mr-2">✨</span>
      <h1 class="text-xl font-bold tracking-wider" style="font-family: 'Cinzel', serif;">
        Design<span class="text-primary">Duel</span>
      </h1>
    </div>
    <div class="navbar-center">
      <ul class="steps steps-horizontal">
        {#each phases as phase (phase.id)}
          <li
            class="step"
            class:step-primary={phase.id === activePhase || phases.findIndex(p => p.id === phase.id) < phases.findIndex(p => p.id === activePhase)}
          >
            <button
              class="btn btn-ghost btn-xs uppercase tracking-widest text-xs"
              class:text-primary={phase.id === activePhase}
              class:font-bold={phase.id === activePhase}
              onclick={() => activePhase = phase.id}
            >
              {phase.icon} {phase.label}
            </button>
          </li>
        {/each}
      </ul>
    </div>
    <div class="navbar-end gap-2">
      <div class="bg-base-200 px-3 py-1 rounded-lg border border-base-300 flex items-center gap-2">
        <span class="text-warning text-sm">⏳</span>
        <span class="font-mono text-sm font-bold">34:12</span>
      </div>
      <button class="btn btn-ghost btn-circle btn-sm">⚙️</button>
      <div class="avatar placeholder">
        <div class="bg-gradient-to-br from-warning to-orange-600 w-8 rounded-full border-2 border-base-100 shadow-md">
          <span class="text-white text-xs font-bold">JS</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Main content -->
  <main class="flex-1 flex overflow-hidden">
    <!-- Left Panel: Problem -->
    <section class="w-[380px] min-w-[350px] max-w-[500px] flex flex-col border-r border-base-300 bg-base-100 overflow-hidden">
      <!-- Tabs -->
      <div role="tablist" class="tabs tabs-border bg-base-200/50">
        <button role="tab" class="tab" class:tab-active={activeTab === 'problem'} onclick={() => activeTab = 'problem'}>📄 Problem</button>
        <button role="tab" class="tab" class:tab-active={activeTab === 'hints'} onclick={() => activeTab = 'hints'}>💡 Hints</button>
        <button role="tab" class="tab" class:tab-active={activeTab === 'history'} onclick={() => activeTab = 'history'}>🕐 History</button>
      </div>

      <!-- Panel Content -->
      <div class="flex-1 overflow-y-auto p-6 space-y-6">
        {#if activeTab === 'problem'}
          <!-- Title + Badge -->
          <div>
            <div class="flex justify-between items-start mb-2">
              <h2 class="text-2xl font-bold" style="font-family: 'Cinzel', serif;">Design a URL Shortener</h2>
              <span class="badge badge-success badge-sm">Easy</span>
            </div>
            <div class="flex gap-2 text-xs text-base-content/60 mb-4">
              <span>📁 TinyURL, Google</span>
              <span># System Design</span>
            </div>
            <p class="text-sm text-base-content/80 leading-relaxed">
              Design a system like TinyURL that takes a long URL and generates a shorter, unique alias for it. This alias redirects to the original URL.
            </p>
          </div>

          <!-- Functional Requirements -->
          <div>
            <h3 class="font-bold text-base mb-3">Functional Requirements:</h3>
            <ul class="space-y-2">
              {#each functionalReqs as req (req)}
                <li class="flex items-start gap-2 text-sm">
                  <span class="text-primary mt-1">•</span>
                  <span>{req}</span>
                </li>
              {/each}
            </ul>
          </div>

          <!-- Non-Functional Requirements -->
          <div>
            <h3 class="font-bold text-base mb-3">Non-Functional Requirements:</h3>
            <ul class="space-y-2">
              {#each nonFunctionalReqs as req (req)}
                <li class="flex items-start gap-2 text-sm">
                  <span class="text-primary mt-1">•</span>
                  <span>{req}</span>
                </li>
              {/each}
            </ul>
          </div>

          <!-- Magical Constraint -->
          <div class="card bg-base-200 border border-base-300">
            <div class="card-body p-4">
              <h4 class="font-bold text-sm flex items-center gap-2">
                <span class="text-warning">⭐</span> Magical Constraint
              </h4>
              <p class="text-xs italic text-base-content/60">
                "Beware, apprentice! The system must handle 100M new URLs per day. Ensure your database sharding strategy is sound, lest the crystal ball cracks under pressure."
              </p>
            </div>
          </div>

          <!-- AI Chat bubble -->
          <div class="border-t border-base-300 pt-4">
            <div class="chat chat-start">
              <div class="chat-image avatar placeholder">
                <div class="bg-indigo-900 w-8 rounded-full">
                  <span class="text-white text-xs">🤖</span>
                </div>
              </div>
              <div class="chat-bubble chat-bubble-neutral text-sm">
                Great start on the requirements. Before we move to the diagram, how would you estimate the storage needed for 5 years?
              </div>
            </div>
          </div>
        {/if}
      </div>

      <!-- Bottom actions -->
      <div class="p-4 border-t border-base-300 bg-base-200/50 flex justify-between items-center">
        <button class="btn btn-ghost btn-sm">‹ Previous</button>
        <div class="flex gap-2">
          <button class="btn btn-outline btn-sm">Ask AI Hint</button>
          <button class="btn btn-primary btn-sm">Next Phase ›</button>
        </div>
      </div>
    </section>

    <!-- Right Panel: Canvas -->
    <section class="flex-1 relative overflow-hidden flex flex-col" style="background-color: oklch(var(--b2));">
      <!-- Toolbar -->
      <div class="absolute top-4 left-1/2 -translate-x-1/2 z-20">
        <div class="join bg-base-100 shadow-lg border border-base-300 rounded-lg">
          {#each tools as tool (tool.label)}
            <button class="join-item btn btn-sm btn-ghost" class:btn-active={tool.active} title={tool.label}>
              {tool.icon}
            </button>
          {/each}
          <div class="divider divider-horizontal m-0 h-8 self-center"></div>
          <button class="join-item btn btn-sm btn-ghost" title="Image">🖼</button>
          <button class="join-item btn btn-sm btn-ghost" title="Add">➕</button>
        </div>
      </div>

      <!-- Dot grid background -->
      <div class="absolute inset-0 opacity-20 z-0" style="background-image: radial-gradient(oklch(var(--bc) / 0.3) 1px, transparent 1px); background-size: 20px 20px;"></div>

      <!-- SVG Diagram -->
      <div class="flex-1 z-10 overflow-auto relative cursor-crosshair flex items-center justify-center">
        <svg width="800" height="500" style="font-family: 'Caveat', cursive;">
          <!-- Client -->
          <g transform="translate(50, 200)">
            <circle cx="20" cy="20" r="15" fill="none" stroke="oklch(var(--bc))" stroke-width="3" opacity="0.6" />
            <path d="M5 50 C 5 35, 35 35, 35 50" fill="none" stroke="oklch(var(--bc))" stroke-width="3" opacity="0.6" />
            <text fill="oklch(var(--bc) / 0.6)" font-size="20" x="0" y="75">Client</text>
          </g>

          <!-- Arrow: Client → LB -->
          <path d="M100 220 L 200 220" fill="none" stroke="oklch(var(--bc) / 0.5)" stroke-dasharray="5,5" stroke-width="2" marker-end="url(#arrowhead)" />

          <!-- Load Balancer -->
          <g transform="translate(220, 180)">
            <rect x="0" y="0" width="80" height="80" rx="4" fill="transparent" stroke="oklch(var(--wa))" stroke-width="3" />
            <text fill="oklch(var(--wa))" font-size="18" x="10" y="45">LB</text>
          </g>

          <!-- Arrow: LB → App Svr 1 -->
          <path d="M300 200 L 380 150" fill="none" stroke="oklch(var(--bc) / 0.5)" stroke-width="2" marker-end="url(#arrowhead)" />
          <!-- Arrow: LB → App Svr 2 -->
          <path d="M300 240 L 380 290" fill="none" stroke="oklch(var(--bc) / 0.5)" stroke-width="2" marker-end="url(#arrowhead)" />

          <!-- App Server 1 -->
          <g transform="translate(400, 100)">
            <rect x="0" y="0" width="120" height="80" rx="4" fill="transparent" stroke="oklch(var(--p))" stroke-width="3" />
            <text fill="oklch(var(--p))" font-size="20" x="15" y="45">App Svr 1</text>
          </g>

          <!-- App Server 2 -->
          <g transform="translate(400, 260)">
            <rect x="0" y="0" width="120" height="80" rx="4" fill="transparent" stroke="oklch(var(--p))" stroke-width="3" />
            <text fill="oklch(var(--p))" font-size="20" x="15" y="45">App Svr 2</text>
          </g>

          <!-- DB Cluster (cylinder shape) -->
          <g transform="translate(600, 150)">
            <path d="M0 20 A 40 10 0 1 1 80 20 A 40 10 0 1 1 0 20 Z" fill="none" stroke="oklch(var(--su))" stroke-width="3" />
            <path d="M0 20 L 0 100 A 40 10 0 1 0 80 100 L 80 20" fill="none" stroke="oklch(var(--su))" stroke-width="3" />
            <text fill="oklch(var(--su))" font-size="18" x="5" y="65">DB Cluster</text>
          </g>

          <!-- Redis (dashed box) -->
          <g transform="translate(600, 330)">
            <rect x="0" y="0" width="100" height="60" rx="4" fill="transparent" stroke="oklch(var(--er))" stroke-dasharray="8,4" stroke-width="3" />
            <text fill="oklch(var(--er))" font-size="20" x="20" y="35">Redis</text>
          </g>

          <!-- Interviewer cursor -->
          <g transform="translate(420, 80)">
            <polygon points="0,0 0,16 5,12 10,20 14,18 9,10 16,10" fill="oklch(var(--wa))" />
            <rect x="20" y="0" rx="4" ry="4" width="85" height="22" fill="oklch(var(--wa))" />
            <text fill="white" font-size="12" x="28" y="15" style="font-family: 'Inter', sans-serif;">Interviewer</text>
          </g>

          <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="oklch(var(--bc) / 0.5)" />
            </marker>
          </defs>
        </svg>
      </div>

      <!-- Mic button -->
      <div class="absolute bottom-6 right-6 z-30">
        <button class="btn btn-circle btn-lg btn-error shadow-lg animate-pulse">🎙️</button>
      </div>

      <!-- Zoom controls -->
      <div class="absolute bottom-6 left-6 z-30">
        <div class="join bg-base-100 border border-base-300 rounded-lg shadow-sm">
          <button class="join-item btn btn-sm btn-ghost" onclick={() => zoom = Math.max(50, zoom - 10)}>−</button>
          <span class="join-item btn btn-sm btn-ghost no-animation font-mono text-xs">{zoom}%</span>
          <button class="join-item btn btn-sm btn-ghost" onclick={() => zoom = Math.min(200, zoom + 10)}>+</button>
        </div>
      </div>
    </section>
  </main>
</div>

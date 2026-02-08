<script>
  import Excalidraw from '$lib/Excalidraw.svelte';

  let activeTab = $state('problem');
  let activePhase = $state('design');

  const phases = [
    { id: 'clarify', label: 'Clarify', icon: 'question_answer' },
    { id: 'estimate', label: 'Estimate', icon: 'calculate' },
    { id: 'design', label: 'Design', icon: 'bolt' },
    { id: 'explain', label: 'Explain', icon: 'record_voice_over' },
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
  <link href="https://fonts.googleapis.com/icon?family=Material+Icons+Round" rel="stylesheet" />
</svelte:head>

<style>
  .shadow-glow {
    box-shadow: 0 0 15px rgba(139, 92, 246, 0.5);
  }
</style>

<div class="h-screen flex flex-col bg-base-300 text-base-content font-sans overflow-hidden" style="font-family: 'Inter', sans-serif;">
  <!-- Navbar -->
  <nav class="h-16 bg-base-100 border-b border-base-300 flex items-center justify-between px-4 shadow-md z-10 shrink-0">
    <div class="flex items-center space-x-2">
      <span class="material-icons-round text-primary text-3xl animate-pulse">auto_fix_high</span>
      <h1 class="text-xl font-bold tracking-wider" style="font-family: 'Cinzel', serif;">
        Design<span class="text-primary">Duel</span>
      </h1>
    </div>
    <div class="flex items-center space-x-1 lg:space-x-4">
      {#each phases as phase, i (phase.id)}
        <div class="flex flex-col items-center" class:opacity-50={phase.id !== activePhase}>
          <button
            class="flex items-center space-x-1 transition-all"
            class:text-primary={phase.id === activePhase}
            onclick={() => activePhase = phase.id}
          >
            <span class="material-icons-round text-sm" class:animate-bounce={phase.id === activePhase}>{phase.icon}</span>
            <span class="text-xs font-semibold uppercase tracking-widest hidden md:block">{phase.label}</span>
          </button>
          <div
            class="h-1 w-16 md:w-24 rounded-full mt-1"
            class:bg-gradient-to-r={phase.id === activePhase}
            class:from-purple-500={phase.id === activePhase}
            class:to-indigo-500={phase.id === activePhase}
            class:shadow-glow={phase.id === activePhase}
            class:bg-base-300={phase.id !== activePhase}
          ></div>
        </div>
        {#if i < phases.length - 1}
          <div class="h-px w-4 md:w-8 bg-base-300"></div>
        {/if}
      {/each}
    </div>
    <div class="flex items-center space-x-4">
      <div class="bg-base-200 px-3 py-1 rounded-md border border-base-300 flex items-center space-x-2">
        <span class="material-icons-round text-warning text-sm">hourglass_top</span>
        <span class="font-mono text-sm font-bold">34:12</span>
      </div>
      <button class="hidden md:flex items-center justify-center w-8 h-8 rounded-full hover:bg-base-200 transition">
        <span class="material-icons-round">settings</span>
      </button>
      <div class="h-8 w-8 rounded-full bg-gradient-to-br from-warning to-orange-600 flex items-center justify-center text-white font-bold text-xs border-2 border-base-100 shadow-md cursor-pointer">
        JS
      </div>
    </div>
  </nav>

  <!-- Main content -->
  <main class="flex-1 flex overflow-hidden">
    <!-- Left Panel: Problem -->
    <section class="w-[380px] min-w-[350px] max-w-[500px] flex flex-col border-r border-base-300 bg-base-100 overflow-hidden">
      <!-- Tabs -->
      <div role="tablist" class="tabs tabs-border bg-base-200/50">
        <button role="tab" class="tab flex items-center gap-2" class:tab-active={activeTab === 'problem'} onclick={() => activeTab = 'problem'}>
          <span class="material-icons-round text-base">description</span>
          <span>Problem</span>
        </button>
        <button role="tab" class="tab flex items-center gap-2" class:tab-active={activeTab === 'hints'} onclick={() => activeTab = 'hints'}>
          <span class="material-icons-round text-base">lightbulb</span>
          <span>Hints</span>
        </button>
        <button role="tab" class="tab flex items-center gap-2" class:tab-active={activeTab === 'history'} onclick={() => activeTab = 'history'}>
          <span class="material-icons-round text-base">history</span>
          <span>History</span>
        </button>
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
            <div class="flex items-center gap-4 text-xs text-base-content/60 mb-4">
              <span class="flex items-center gap-1">
                <span class="material-icons-round text-sm">business</span>
                TinyURL, Google
              </span>
              <span class="flex items-center gap-1">
                <span class="material-icons-round text-sm">tag</span>
                System Design
              </span>
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
                <span class="material-icons-round text-warning">stars</span>
                Magical Constraint
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
                <div class="bg-indigo-900 w-8 rounded-full flex items-center justify-center">
                  <span class="material-icons-round text-white text-sm">smart_toy</span>
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
        <button class="btn btn-ghost btn-sm">
          <span class="material-icons-round text-base">chevron_left</span>
          Previous
        </button>
        <div class="flex gap-2">
          <button class="btn btn-outline btn-sm">Ask AI Hint</button>
          <button class="btn btn-primary btn-sm">
            Next Phase
            <span class="material-icons-round text-sm">chevron_right</span>
          </button>
        </div>
      </div>
    </section>

    <!-- Right Panel: Excalidraw Canvas -->
    <section class="flex-1 relative overflow-hidden">
      <Excalidraw theme="dark" />
      <div class="absolute bottom-6 left-1/2 -translate-x-1/2 z-50">
        <button class="btn btn-circle btn-lg btn-error shadow-lg animate-pulse">
          <span class="material-icons-round text-2xl">mic</span>
        </button>
      </div>
    </section>
  </main>
</div>

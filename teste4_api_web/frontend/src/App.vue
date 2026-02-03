<template>
  <div id="app">
    <header>
      <h1>Operadoras ANS</h1>
      <nav>
        <router-link to="/">Listagem</router-link>
      </nav>
    </header>
    <main>
      <router-view v-slot="{ Component }">
        <template v-if="Component">
          <Suspense>
            <component :is="Component" />
            <template #fallback>Carregando...</template>
          </Suspense>
        </template>
      </router-view>
    </main>
  </div>
</template>

<script setup>
</script>

<style>
  * { box-sizing: border-box; }
  body { margin: 0; font-family: system-ui, sans-serif; background: #f5f5f5; }
  #app { min-height: 100vh; }
  header {
    background: #1a365d;
    color: #fff;
    padding: 1rem 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  header h1 { margin: 0; font-size: 1.25rem; }
  header a { color: #90cdf4; text-decoration: none; }
  header a:hover { text-decoration: underline; }
  main { padding: 1.5rem 2rem; max-width: 1200px; margin: 0 auto; }
  .loading { color: #666; }
  .error { color: #c53030; }
  .table-wrapper {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    margin: 0 -0.25rem;
  }
  table { width: 100%; min-width: 600px; border-collapse: collapse; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  th, td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #e2e8f0; }
  th { background: #edf2f7; font-weight: 600; }
  tr:hover { background: #f7fafc; }
  .pagination { margin-top: 1rem; display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
  .pagination button {
    padding: 0.5rem 0.75rem;
    min-height: 44px;
    border: 1px solid #cbd5e0;
    background: #fff;
    cursor: pointer;
    border-radius: 4px;
  }
  .pagination button:hover:not(:disabled) { background: #edf2f7; }
  .pagination button:disabled { opacity: 0.5; cursor: not-allowed; }
  .search { margin-bottom: 1rem; }
  .search input { padding: 0.5rem 0.75rem; width: 100%; max-width: 400px; border: 1px solid #cbd5e0; border-radius: 4px; font-size: 16px; }
  .chart-container {
    width: 100%;
    max-width: 100%;
    min-height: 380px;
    margin: 2rem 0;
    background: #fff;
    padding: 1.25rem;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  }
  .card { background: #fff; padding: 1.5rem; margin-bottom: 1rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  .back-link { display: inline-block; margin-bottom: 1rem; padding: 0.5rem 0; min-height: 44px; color: #3182ce; text-decoration: none; }
  .back-link:hover { text-decoration: underline; }

  @media (max-width: 768px) {
    header { padding: 0.75rem 1rem; flex-wrap: wrap; gap: 0.5rem; }
    header h1 { font-size: 1.1rem; }
    main { padding: 1rem; }
    .search input { max-width: none; }
    .chart-container { min-height: 280px; padding: 0.75rem; }
    .card { padding: 1rem; }
    th, td { padding: 0.5rem 0.4rem; font-size: 0.9rem; }
    table { min-width: 520px; }
  }

  @media (max-width: 480px) {
    header { padding: 0.5rem 0.75rem; }
    main { padding: 0.75rem; }
    .chart-container { min-height: 240px; }
  }
</style>

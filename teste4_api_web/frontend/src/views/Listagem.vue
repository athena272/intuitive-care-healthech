<template>
  <div>
    <h2>Operadoras</h2>
    <div class="search">
      <input
        v-model="filtro"
        type="text"
        placeholder="Filtrar por razao social ou CNPJ"
        @input="aplicarFiltro"
      />
    </div>
    <p v-if="erro" class="error">{{ erro }}</p>
    <p v-else-if="loading" class="loading">Carregando operadoras...</p>
    <template v-else>
      <table>
        <thead>
          <tr>
            <th>CNPJ</th>
            <th>Razao Social</th>
            <th>Valor total (R$)</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="op in itensFiltrados" :key="op.cnpj">
            <td>{{ formatCnpj(op.cnpj) }}</td>
            <td>{{ op.razao_social }}</td>
            <td>{{ formatValor(op.valor_total) }}</td>
            <td>
              <router-link :to="'/operadora/' + op.cnpj">Detalhes</router-link>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="!itensFiltrados.length && lista.length" class="loading">Nenhum resultado para o filtro.</div>
      <div class="pagination">
        <button :disabled="page <= 1" @click="page--; carregar()">Anterior</button>
        <span>Pagina {{ page }} de {{ totalPaginas }}</span>
        <button :disabled="page >= totalPaginas" @click="page++; carregar()">Proxima</button>
      </div>
    </template>

    <h3>Despesas por UF</h3>
    <div v-if="stats" class="chart-container">
      <canvas ref="chartCanvas"></canvas>
    </div>
    <p v-else-if="!loadingStats && !stats" class="loading">Nenhum dado de estatisticas.</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from "vue";
import { getOperadoras, getEstatisticas, formatCnpj } from "../api";
import { Chart, registerables } from "chart.js";

Chart.register(...registerables);

const loading = ref(true);
const loadingStats = ref(true);
const erro = ref("");
const lista = ref([]);
const total = ref(0);
const page = ref(1);
const limit = 10;
const filtro = ref("");
const stats = ref(null);
const chartCanvas = ref(null);
let chartInstance = null;

const totalPaginas = computed(() => Math.max(1, Math.ceil(total.value / limit)));

const itensFiltrados = computed(() => {
  const f = filtro.value.trim().toLowerCase();
  if (!f) return lista.value;
  return lista.value.filter(
    (op) =>
      (op.razao_social && op.razao_social.toLowerCase().includes(f)) ||
      (op.cnpj && String(op.cnpj).replace(/\D/g, "").includes(f.replace(/\D/g, "")))
  );
});

function formatValor(v) {
  if (v == null) return "-";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v);
}

function aplicarFiltro() {
  // Filtro aplicado em memoria na pagina atual (busca no cliente)
}

async function carregar() {
  loading.value = true;
  erro.value = "";
  try {
    const res = await getOperadoras(page.value, limit);
    lista.value = res.data || [];
    total.value = res.total ?? 0;
  } catch (e) {
    erro.value = e.response?.data?.detail || e.message || "Erro ao carregar.";
  } finally {
    loading.value = false;
  }
}

async function carregarStats() {
  loadingStats.value = true;
  try {
    stats.value = await getEstatisticas();
    await nextTick();
    if (stats.value?.despesas_por_uf?.length && chartCanvas.value) {
      const ctx = chartCanvas.value.getContext("2d");
      if (chartInstance) chartInstance.destroy();
      chartInstance = new Chart(ctx, {
        type: "bar",
        data: {
          labels: stats.value.despesas_por_uf.map((x) => x.uf),
          datasets: [
            {
              label: "Total despesas (R$)",
              data: stats.value.despesas_por_uf.map((x) => x.total),
              backgroundColor: "rgba(49, 130, 206, 0.6)",
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          aspectRatio: 1.8,
          plugins: { legend: { display: false } },
          scales: {
            y: { beginAtZero: true },
            x: { ticks: { maxRotation: 45, minRotation: 0 } },
          },
        },
      });
    }
  } catch (_) {
    stats.value = null;
  } finally {
    loadingStats.value = false;
  }
}

onMounted(() => {
  carregar();
  carregarStats();
});

</script>

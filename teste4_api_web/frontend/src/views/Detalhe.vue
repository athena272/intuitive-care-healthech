<template>
  <div>
    <router-link to="/" class="back-link">Voltar à listagem</router-link>
    <p v-if="erro" class="error">{{ erro }}</p>
    <p v-else-if="loading" class="loading">Carregando...</p>
    <template v-else-if="operadora">
      <div class="card">
        <h2>{{ operadora.razao_social }}</h2>
        <p><strong>CNPJ:</strong> {{ formatCnpj(operadora.cnpj) }}</p>
        <p v-if="operadora.registro_ans"><strong>Registro ANS:</strong> {{ operadora.registro_ans }}</p>
        <p v-if="operadora.uf"><strong>UF:</strong> {{ operadora.uf }}</p>
        <p v-if="operadora.modalidade"><strong>Modalidade:</strong> {{ operadora.modalidade }}</p>
      </div>
      <div class="card">
        <h3>Histórico de despesas por trimestre</h3>
        <div v-if="despesas.length" class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Ano</th>
                <th>Trimestre</th>
                <th>Valor (R$)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="d in despesas" :key="d.ano + '-' + d.trimestre">
                <td>{{ d.ano }}</td>
                <td>{{ d.trimestre }}</td>
                <td>{{ formatValor(d.valor_despesas) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else class="loading">Nenhum dado de despesas.</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute } from "vue-router";
import { getOperadoraByCnpj, getDespesasOperadora, formatCnpj } from "../api";

const route = useRoute();
const cnpj = computed(() => route.params.cnpj || "");
const loading = ref(true);
const erro = ref("");
const operadora = ref(null);
const despesas = ref([]);

function formatValor(v) {
  if (v == null) return "-";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v);
}

onMounted(async () => {
  if (!cnpj.value) {
    erro.value = "CNPJ nao informado.";
    loading.value = false;
    return;
  }
  try {
    operadora.value = await getOperadoraByCnpj(cnpj.value);
    const res = await getDespesasOperadora(cnpj.value);
    despesas.value = res.data || [];
  } catch (e) {
    erro.value = e.response?.status === 404 ? "Operadora nao encontrada." : (e.message || "Erro ao carregar.");
  } finally {
    loading.value = false;
  }
});
</script>

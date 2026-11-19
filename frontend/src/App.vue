<script setup lang="ts">
import { onMounted, ref } from 'vue'

const health = ref<string>('…')
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    const res = await fetch('/api/health')
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`)
    }
    const data = (await res.json()) as { status: string }
    health.value = data.status
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
    health.value = 'down'
  }
})
</script>

<template>
  <main class="page">
    <h1>Keitaro Wrapper</h1>
    <p class="hint">Vue + FastAPI monorepo skeleton</p>
    <p>
      Backend health:
      <strong :class="error ? 'bad' : 'ok'">{{ health }}</strong>
    </p>
    <p v-if="error" class="err">{{ error }}</p>
  </main>
</template>

<style scoped>
.page {
  font-family: system-ui, sans-serif;
  max-width: 40rem;
  margin: 3rem auto;
  padding: 0 1rem;
}
.hint {
  color: #666;
}
.ok {
  color: #0a7a2f;
}
.bad {
  color: #b00020;
}
.err {
  color: #b00020;
  font-size: 0.9rem;
}
</style>

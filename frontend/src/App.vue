<script setup lang="ts">
import { onMounted, ref } from 'vue'
import CreateCampaignForm, {
  type CreatedCampaign,
} from './components/CreateCampaignForm.vue'
import StreamsEditor from './components/StreamsEditor.vue'

const health = ref<string>('…')
const campaigns = ref<CreatedCampaign[]>([])
const listError = ref<string | null>(null)
const selectedCampaignId = ref<string | null>(null)

onMounted(async () => {
  try {
    const res = await fetch('/api/health')
    health.value = res.ok ? ((await res.json()) as { status: string }).status : 'down'
  } catch {
    health.value = 'down'
  }
  await loadCampaigns()
})

async function loadCampaigns() {
  listError.value = null
  try {
    const res = await fetch('/api/campaigns')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    campaigns.value = (await res.json()) as CreatedCampaign[]
  } catch (e) {
    listError.value = e instanceof Error ? e.message : String(e)
  }
}

function onCreated(campaign: CreatedCampaign) {
  campaigns.value = [campaign, ...campaigns.value]
  selectedCampaignId.value = campaign.id
}
</script>

<template>
  <main class="page">
    <header class="header">
      <h1>Keitaro Wrapper</h1>
      <p class="hint">Backend health: <strong>{{ health }}</strong></p>
    </header>

    <StreamsEditor
      v-if="selectedCampaignId"
      :campaign-id="selectedCampaignId"
      @close="selectedCampaignId = null"
    />

    <template v-else>
      <CreateCampaignForm @created="onCreated" />

      <section class="list">
        <h2>Created campaigns</h2>
        <p v-if="listError" class="err">{{ listError }}</p>
        <p v-else-if="!campaigns.length" class="hint">No local campaigns yet.</p>
        <ul v-else>
          <li v-for="c in campaigns" :key="c.id">
            <button type="button" class="camp" @click="selectedCampaignId = c.id">
              <strong>{{ c.name }}</strong>
              — geo {{ c.geo }}, offer {{ c.offer_id }}, KT #{{ c.keitaro_campaign_id }}
            </button>
          </li>
        </ul>
      </section>
    </template>
  </main>
</template>

<style scoped>
.page {
  font-family: system-ui, sans-serif;
  max-width: 52rem;
  margin: 2rem auto;
  padding: 0 1rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.header h1 {
  margin: 0 0 0.35rem;
}

.hint {
  margin: 0;
  color: #666;
}

.list h2 {
  margin: 0 0 0.75rem;
  font-size: 1.1rem;
}

.list ul {
  margin: 0;
  padding: 0;
  list-style: none;
}

.camp {
  width: 100%;
  text-align: left;
  border: 1px solid #ddd;
  background: #fff;
  border-radius: 4px;
  padding: 0.65rem 0.75rem;
  margin-bottom: 0.4rem;
  font: inherit;
  cursor: pointer;
}

.camp:hover {
  background: #f5f8ff;
}

.err {
  color: #b00020;
}
</style>

<script setup lang="ts">
import {
  NBadge,
  NConfigProvider,
  NMessageProvider,
  NSpace,
  NTag,
  NText,
} from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import CreateCampaignForm, {
  type CreatedCampaign,
} from './components/CreateCampaignForm.vue'
import StreamsEditor from './components/StreamsEditor.vue'
import { themeOverrides } from './theme'

const health = ref<string>('…')
const campaigns = ref<CreatedCampaign[]>([])
const listError = ref<string | null>(null)
const selectedCampaignId = ref<string | null>(null)

const healthOk = computed(() => health.value === 'ok')

onMounted(async () => {
  try {
    const res = await fetch('/api/health')
    health.value = res.ok
      ? ((await res.json()) as { status: string }).status
      : 'down'
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
  <NConfigProvider :theme-overrides="themeOverrides">
    <NMessageProvider>
      <div class="shell">
        <header class="brand">
          <div>
            <p class="eyebrow">Ad tracking toolkit</p>
            <h1>Keitaro Wrapper</h1>
            <p class="lede">
              Создавай кампании и аккуратно правь офферы в потоках — без лишнего шума.
            </p>
          </div>
          <NTag :type="healthOk ? 'success' : 'error'" round size="small">
            API {{ health }}
          </NTag>
        </header>

        <StreamsEditor
          v-if="selectedCampaignId"
          :campaign-id="selectedCampaignId"
          @close="selectedCampaignId = null"
        />

        <template v-else>
          <div class="layout">
            <section class="panel">
              <CreateCampaignForm @created="onCreated" />
            </section>

            <section class="panel">
              <div class="panel-head">
                <h2>Кампании</h2>
                <NBadge :value="campaigns.length" :max="99" type="info" />
              </div>

              <NText v-if="listError" type="error">{{ listError }}</NText>
              <NText v-else-if="!campaigns.length" depth="3">
                Пока пусто — создай первую кампанию слева.
              </NText>

              <NSpace v-else vertical :size="10">
                <button
                  v-for="c in campaigns"
                  :key="c.id"
                  type="button"
                  class="camp"
                  @click="selectedCampaignId = c.id"
                >
                  <span class="camp-name">{{ c.name }}</span>
                  <span class="camp-meta">
                    geo {{ c.geo }} · offer {{ c.offer_id }} · KT #{{ c.keitaro_campaign_id }}
                  </span>
                </button>
              </NSpace>
            </section>
          </div>
        </template>
      </div>
    </NMessageProvider>
  </NConfigProvider>
</template>

<style scoped>
.shell {
  position: relative;
  z-index: 1;
  max-width: 960px;
  margin: 0 auto;
  padding: 2.5rem 1.25rem 3.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
}

.brand {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.eyebrow {
  margin: 0 0 0.35rem;
  font-size: 0.8rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
  font-weight: 600;
}

.brand h1 {
  margin: 0;
  font-size: clamp(2rem, 4vw, 2.6rem);
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.1;
}

.lede {
  margin: 0.65rem 0 0;
  max-width: 34rem;
  color: var(--muted);
  line-height: 1.5;
}

.layout {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 1.25rem;
}

@media (max-width: 820px) {
  .layout {
    grid-template-columns: 1fr;
  }
}

.panel {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 1.25rem 1.35rem 1.4rem;
  backdrop-filter: blur(10px);
  box-shadow: 0 12px 40px rgba(28, 25, 23, 0.05);
}

.panel-head {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  margin-bottom: 1rem;
}

.panel-head h2 {
  margin: 0;
  font-size: 1.15rem;
  letter-spacing: -0.02em;
}

.camp {
  width: 100%;
  text-align: left;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.72);
  border-radius: 12px;
  padding: 0.85rem 0.95rem;
  font: inherit;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    transform 0.15s ease,
    background 0.15s ease;
}

.camp:hover {
  border-color: #99f6e4;
  background: #fff;
  transform: translateY(-1px);
}

.camp-name {
  display: block;
  font-weight: 600;
  margin-bottom: 0.2rem;
}

.camp-meta {
  display: block;
  color: var(--muted);
  font-size: 0.88rem;
}
</style>

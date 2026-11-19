<script setup lang="ts">
import { computed, ref, watch } from 'vue'

export type CreatedCampaign = {
  id: string
  name: string
  geo: string
  offer_id: number
  keitaro_campaign_id: number
  keitaro_alias: string
}

type OfferSuggestion = {
  id: number
  name: string
}

const emit = defineEmits<{
  created: [campaign: CreatedCampaign]
}>()

const name = ref('')
const geo = ref('')
const offerQuery = ref('')
const selectedOffer = ref<OfferSuggestion | null>(null)
const suggestions = ref<OfferSuggestion[]>([])
const loading = ref(false)
const searching = ref(false)
const error = ref<string | null>(null)
const success = ref<string | null>(null)

const canSubmit = computed(
  () =>
    name.value.trim().length > 0 &&
    geo.value.trim().length >= 2 &&
    selectedOffer.value !== null &&
    !loading.value,
)

let searchTimer: ReturnType<typeof setTimeout> | null = null

watch(offerQuery, (value) => {
  selectedOffer.value = null
  if (searchTimer) clearTimeout(searchTimer)
  const q = value.trim()
  if (q.length < 1) {
    suggestions.value = []
    return
  }
  searchTimer = setTimeout(() => void searchOffers(q), 250)
})

async function searchOffers(q: string) {
  searching.value = true
  error.value = null
  try {
    const res = await fetch(`/api/offers/search?q=${encodeURIComponent(q)}`)
    if (!res.ok) {
      const body = await res.json().catch(() => null)
      throw new Error(formatError(body) || `Search failed (${res.status})`)
    }
    suggestions.value = (await res.json()) as OfferSuggestion[]
  } catch (e) {
    suggestions.value = []
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    searching.value = false
  }
}

function pickOffer(offer: OfferSuggestion) {
  selectedOffer.value = offer
  offerQuery.value = `${offer.id} — ${offer.name}`
  suggestions.value = []
}

async function onSubmit() {
  if (!selectedOffer.value || !canSubmit.value) return
  loading.value = true
  error.value = null
  success.value = null
  try {
    const res = await fetch('/api/campaigns', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name.value.trim(),
        geo: geo.value.trim(),
        offer_id: selectedOffer.value.id,
      }),
    })
    const body = await res.json().catch(() => null)
    if (!res.ok) {
      throw new Error(formatError(body) || `Create failed (${res.status})`)
    }
    const campaign = body as CreatedCampaign
    success.value = `Created in Keitaro #${campaign.keitaro_campaign_id} (alias: ${campaign.keitaro_alias})`
    emit('created', campaign)
    name.value = ''
    geo.value = ''
    offerQuery.value = ''
    selectedOffer.value = null
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

function formatError(body: unknown): string | null {
  if (!body || typeof body !== 'object') return null
  const detail = (body as { detail?: unknown }).detail
  if (typeof detail === 'string') return detail
  if (detail && typeof detail === 'object' && 'message' in detail) {
    return String((detail as { message: unknown }).message)
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => (typeof item === 'object' && item && 'msg' in item ? String(item.msg) : String(item)))
      .join('; ')
  }
  return null
}
</script>

<template>
  <form class="form" @submit.prevent="onSubmit">
    <h2>New campaign</h2>

    <label class="field">
      <span>Name</span>
      <input v-model="name" type="text" placeholder="имя кампании" required />
    </label>

    <label class="field">
      <span>Geo</span>
      <input v-model="geo" type="text" placeholder="MX, AU, RO, ..." required />
    </label>

    <div class="field">
      <span>Offer</span>
      <input
        v-model="offerQuery"
        type="text"
        placeholder="поиск по офферам с автокомплитом"
        autocomplete="off"
      />
      <p v-if="searching" class="meta">Searching…</p>
      <ul v-if="suggestions.length" class="suggest">
        <li v-for="offer in suggestions" :key="offer.id">
          <button type="button" @click="pickOffer(offer)">
            <strong>{{ offer.id }}</strong> — {{ offer.name }}
          </button>
        </li>
      </ul>
      <p v-if="selectedOffer" class="meta ok">
        Selected: #{{ selectedOffer.id }}
      </p>
    </div>

    <button class="submit" type="submit" :disabled="!canSubmit">
      {{ loading ? 'Creating…' : 'Create' }}
    </button>

    <p v-if="error" class="msg err">{{ error }}</p>
    <p v-if="success" class="msg ok">{{ success }}</p>
  </form>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-width: 28rem;
}

h2 {
  margin: 0;
  font-size: 1.4rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.field > span {
  font-size: 0.85rem;
  color: #444;
}

input {
  border: 1px solid #c8c8c8;
  border-radius: 4px;
  padding: 0.55rem 0.65rem;
  font: inherit;
}

.suggest {
  list-style: none;
  margin: 0;
  padding: 0;
  border: 1px solid #ddd;
  border-radius: 4px;
  max-height: 12rem;
  overflow: auto;
}

.suggest button {
  width: 100%;
  text-align: left;
  border: 0;
  background: #fff;
  padding: 0.5rem 0.65rem;
  font: inherit;
  cursor: pointer;
}

.suggest button:hover {
  background: #f3f7ff;
}

.submit {
  border: 1px solid #9db7e8;
  background: #cfe0ff;
  border-radius: 4px;
  padding: 0.7rem 1rem;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.submit:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.meta {
  margin: 0;
  font-size: 0.85rem;
  color: #666;
}

.msg {
  margin: 0;
  font-size: 0.9rem;
}

.ok {
  color: #0a7a2f;
}

.err {
  color: #b00020;
}
</style>

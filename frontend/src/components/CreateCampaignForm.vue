<script setup lang="ts">
import {
  NAlert,
  NAutoComplete,
  NButton,
  NForm,
  NFormItem,
  NInput,
  NSpace,
  NText,
} from 'naive-ui'
import { computed, ref, watch } from 'vue'
import { formatApiError } from '../utils/errors'

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

const offerOptions = computed(() =>
  suggestions.value.map((offer) => ({
    label: `${offer.id} — ${offer.name}`,
    value: String(offer.id),
  })),
)

let searchTimer: ReturnType<typeof setTimeout> | null = null

watch(offerQuery, (value) => {
  if (selectedOffer.value && value === `${selectedOffer.value.id} — ${selectedOffer.value.name}`) {
    return
  }
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
      throw new Error(formatApiError(body) || `Search failed (${res.status})`)
    }
    suggestions.value = (await res.json()) as OfferSuggestion[]
  } catch (e) {
    suggestions.value = []
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    searching.value = false
  }
}

function onSelectOffer(value: string) {
  const offer = suggestions.value.find((item) => String(item.id) === value)
  if (!offer) return
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
      throw new Error(formatApiError(body) || `Create failed (${res.status})`)
    }
    const campaign = body as CreatedCampaign
    success.value = `Кампания создана в Keitaro #${campaign.keitaro_campaign_id} (${campaign.keitaro_alias})`
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
</script>

<template>
  <div>
    <h2 class="title">New campaign</h2>
    <NText depth="3" class="subtitle">
      Имя, гео-фильтр на Google и оффер для остального трафика.
    </NText>

    <NForm class="form" @submit.prevent="onSubmit">
      <NFormItem label="Name" :show-feedback="false">
        <NInput v-model:value="name" placeholder="имя кампании" clearable />
      </NFormItem>

      <NFormItem label="Geo" :show-feedback="false">
        <NInput v-model:value="geo" placeholder="AU, MX, RO…" clearable />
      </NFormItem>

      <NFormItem label="Offer" :show-feedback="false">
        <NAutoComplete
          v-model:value="offerQuery"
          :options="offerOptions"
          :loading="searching"
          placeholder="поиск по офферам с автокомплитом"
          clearable
          blur-after-select
          @select="onSelectOffer"
        />
      </NFormItem>

      <NSpace vertical :size="12">
        <NText v-if="selectedOffer" depth="3">
          Выбран оффер #{{ selectedOffer.id }}
        </NText>
        <NButton
          type="primary"
          attr-type="submit"
          block
          size="large"
          :disabled="!canSubmit"
          :loading="loading"
        >
          Create
        </NButton>
      </NSpace>
    </NForm>

    <NAlert v-if="error" class="alert" type="error" :bordered="false">
      {{ error }}
    </NAlert>
    <NAlert v-if="success" class="alert" type="success" :bordered="false">
      {{ success }}
    </NAlert>
  </div>
</template>

<style scoped>
.title {
  margin: 0;
  font-size: 1.25rem;
  letter-spacing: -0.02em;
}

.subtitle {
  display: block;
  margin: 0.35rem 0 1rem;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.alert {
  margin-top: 1rem;
}
</style>

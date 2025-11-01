'use client'

import { useEffect, useState } from 'react'
import { Select } from '@/components/ui/select'
import { apiClient } from '@/lib/api'
import type { TherapyTechnique } from '@/types'

interface TechniqueSelectorProps {
  value?: string
  onChange: (value: string) => void
}

// Fallback techniques if API fails
const FALLBACK_TECHNIQUES: TherapyTechnique[] = [
  { id: 'cbt', name: 'Kognitive Verhaltenstherapie (CBT)', category: 'CBT', description: 'Fokus auf Gedankenmuster' },
  { id: 'dbt', name: 'Dialektisch-Behaviorale Therapie (DBT)', category: 'DBT', description: 'Emotionsregulation' },
  { id: 'mindfulness', name: 'Achtsamkeit', category: 'Mindfulness', description: 'Präsenz im Moment' },
  { id: 'grounding', name: 'Erdungstechniken', category: 'Grounding', description: 'Körperliche Präsenz' },
  { id: 'breathing', name: 'Atemübungen', category: 'Breathing', description: 'Atemkontrolle' },
  { id: 'journaling', name: 'Journaling', category: 'Writing', description: 'Schriftliche Reflexion' },
  { id: 'progressive-relaxation', name: 'Progressive Muskelentspannung', category: 'Relaxation', description: 'Körperliche Entspannung' },
  { id: 'exposure', name: 'Expositionstherapie', category: 'Exposure', description: 'Graduelle Konfrontation' },
]

export function TechniqueSelector({ value, onChange }: TechniqueSelectorProps) {
  const [techniques, setTechniques] = useState<TherapyTechnique[]>(FALLBACK_TECHNIQUES)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    fetchTechniques()
  }, [])

  const fetchTechniques = async () => {
    try {
      setIsLoading(true)
      const data = await apiClient.getTherapyTechniques()
      if (data && data.length > 0) {
        setTechniques(data)
      }
    } catch (err) {
      console.error('Failed to fetch techniques, using fallback:', err)
      // Keep fallback techniques
    } finally {
      setIsLoading(false)
    }
  }

  // Group by category
  const groupedTechniques = techniques.reduce((acc, tech) => {
    if (!acc[tech.category]) {
      acc[tech.category] = []
    }
    acc[tech.category].push(tech)
    return acc
  }, {} as Record<string, TherapyTechnique[]>)

  return (
    <Select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={isLoading}
    >
      <option value="">Technik auswählen (optional)</option>
      {Object.entries(groupedTechniques).map(([category, techs]) => (
        <optgroup key={category} label={category}>
          {techs.map((tech) => (
            <option key={tech.id} value={tech.id}>
              {tech.name}
            </option>
          ))}
        </optgroup>
      ))}
    </Select>
  )
}

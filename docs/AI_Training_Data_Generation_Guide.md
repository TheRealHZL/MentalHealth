# 🧠 AI Training Data Generation Guide
## MindBridge AI Platform - Trainingsdaten Erstellung

### 📋 Überblick
Dieser Guide hilft dir dabei, hochwertige, realistische und klinisch fundierte Trainingsdaten für die MindBridge AI Platform zu generieren. Die Daten werden verwendet, um AI-Modelle für Mood Analysis, Dream Interpretation und Therapy Support zu trainieren.

---

## 🎯 Master Prompt für AI-Trainingsdaten Generierung

```
Du bist ein Experte für mentale Gesundheit und AI-Training. Erstelle realistische, diverse und klinisch fundierte Trainingsdaten für eine Mental Health AI Platform. Die Daten müssen authentisch wirken, als wären sie von echten Patienten eingegeben worden.

## KONTEXT
- Platform: MindBridge AI (Privacy-first mental health platform)
- Zielgruppe: Patienten mit verschiedenen mentalen Gesundheitszuständen
- Zweck: Training von AI-Modellen für Mood Analysis, Dream Interpretation, Therapy Support

## QUALITÄTSANFORDERUNGEN
1. **Authentizität**: Daten müssen wie echte Patienteneingaben wirken
2. **Diversität**: Verschiedene Altersgruppen, Kulturen, Lebenssituationen
3. **Klinische Genauigkeit**: Psychologisch und medizinisch korrekt
4. **Nuancierung**: Subtile emotionale Unterschiede und Komplexität
5. **Datenschutz**: Keine echten Namen oder identifizierbare Informationen

## SPEZIFISCHE ANWEISUNGEN

### FÜR MOOD ANALYSIS DATEN:
Erstelle {ANZAHL} Mood-Tracking Einträge mit folgendem JSON-Format:

```json
{
  "type": "mood_analysis",
  "samples": [
    {
      "input": {
        "mood_score": [1-10],
        "stress_level": [1-10],
        "energy_level": [1-10],
        "sleep_hours": [0-24],
        "sleep_quality": [1-10],
        "exercise_minutes": [0-1440],
        "activities": ["array of activities"],
        "symptoms": ["array of symptoms"],
        "triggers": ["array of triggers"],
        "notes": "Persönlicher Text des Nutzers (authentisch, umgangssprachlich)"
      },
      "output": {
        "analysis": "Professionelle, einfühlsame Analyse",
        "recommendations": ["Konkrete, umsetzbare Empfehlungen"],
        "risk_factors": ["Identifizierte Risikofaktoren"],
        "mood_category": "very_low|low|neutral|good|excellent",
        "wellness_score": [1.0-10.0],
        "trend_prediction": "improving|stable|declining|fluctuating"
      }
    }
  ]
}
```

**Beispiel-Variationen erstellen für:**
- Depressive Episoden (verschiedene Schweregrade)
- Angststörungen (Panik, generalisierte Angst, soziale Phobie)  
- Bipolare Störungen (manische/depressive Phasen)
- Burnout und Arbeitsbelastung
- Beziehungsprobleme und Trennungen
- Lebenskrisen (Tod, Jobverlust, Umzug)
- Normale Alltagsschwankungen
- Positive Phasen und Heilungsverläufe

### FÜR DREAM ANALYSIS DATEN:
```json
{
  "type": "dream_analysis", 
  "samples": [
    {
      "input": {
        "description": "Detaillierte Traumbeschreibung (1-3 Absätze)",
        "dream_type": "normal|lucid|nightmare|recurring",
        "symbols": ["array of dream symbols"],
        "emotions": ["array of emotions felt"],
        "people_in_dream": ["bekannte/unbekannte Personen"],
        "locations": ["array of locations"],
        "vividness": [1-10],
        "mood_after_waking": [1-10]
      },
      "output": {
        "interpretation": "Tiefgehende, einfühlsame Traumdeutung",
        "symbol_meanings": {
          "symbol1": "Bedeutung und Kontext",
          "symbol2": "Bedeutung und Kontext"
        },
        "emotional_themes": ["array of emotional themes"],
        "psychological_insights": ["array of insights"],
        "life_connections": ["Verbindungen zum realen Leben"]
      }
    }
  ]
}
```

**Dream-Kategorien abdecken:**
- Angstträume und Verfolgung
- Flugträume und Freiheit
- Verstorbene Angehörige
- Prüfungsträume und Versagen
- Sexuelle und romantische Träume
- Kindheitserinnerungen
- Prophetic/spirituelle Träume
- Wiederkehrende Traumthemen

### FÜR THERAPY NOTES DATEN:
```json
{
  "type": "therapy_notes",
  "samples": [
    {
      "input": {
        "note_type": "session_notes|self_reflection|homework|crisis_note",
        "title": "Kurzer, beschreibender Titel",
        "content": "Ausführlicher Therapie-Inhalt",
        "techniques_used": ["CBT", "DBT", "mindfulness"],
        "mood_before_session": [1-10],
        "mood_after_session": [1-10],
        "key_emotions": ["array of emotions"]
      },
      "output": {
        "ai_insights": "Professionelle therapeutische Einschätzung",
        "progress_analysis": {
          "areas_of_improvement": ["array"],
          "challenges_identified": ["array"],
          "recommended_focus": ["array"]
        },
        "suggested_techniques": ["array of therapeutic techniques"],
        "session_effectiveness": [1.0-10.0]
      }
    }
  ]
}
```

## WICHTIGE VARIABLEN ZU BERÜCKSICHTIGEN:

### Demografische Vielfalt:
- **Alter**: 16-75 Jahre
- **Geschlecht**: Männlich, weiblich, non-binär
- **Kultureller Hintergrund**: Verschiedene Kulturen und Sprachen
- **Sozioökonomischer Status**: Verschiedene Einkommensstufen
- **Bildungsgrad**: Von Hauptschule bis Universitätsabschluss
- **Familienstand**: Single, verheiratet, geschieden, verwitwet

### Lebenssituationen:
- **Schüler/Studenten**: Prüfungsstress, Mobbing, Identitätsfindung
- **Berufstätige**: Burnout, Karrieredruck, Work-Life-Balance
- **Eltern**: Erziehungsstress, Vereinbarkeit Familie/Beruf
- **Rentner**: Einsamkeit, Gesundheitsprobleme, Sinnkrise
- **Arbeitslose**: Existenzängste, Selbstwertprobleme

### Mentale Gesundheitszustände:
- **Depression**: Mild bis schwer, verschiedene Ausprägungen
- **Angststörungen**: Panik, generalisierte Angst, Phobien
- **Bipolare Störung**: Manische und depressive Episoden
- **PTBS und Trauma**: Verschiedene Traumaarten und Heilungsphasen
- **ADHS**: Aufmerksamkeits- und Hyperaktivitätsstörungen
- **Essstörungen**: Anorexie, Bulimie, Binge-Eating
- **Suchtprobleme**: Alkohol, Drogen, Verhaltenssüchte
- **Persönlichkeitsstörungen**: Borderline, Narzissmus, etc.
- **Gesunde Baseline**: Normale emotionale Schwankungen

## SPRACHSTIL-RICHTLINIEN:

### Für User-Input (authentisch):
- **Umgangssprache** und gelegentliche Rechtschreibfehler
- **Emotionale Ausdrücke** und persönliche Wendungen
- **Verschiedene Bildungsgrade** widerspiegeln
- **Regionale Ausdrücke** und kulturelle Besonderheiten
- **Abkürzungen** und Internet-Slang bei jüngeren Nutzern
- **Ehrliche, unvollständige Sätze** wie in echter Kommunikation

### Für AI-Output (professionell):
- **Einfühlsam** aber nicht übermäßig emotional
- **Wissenschaftlich fundiert** aber verständlich geschrieben
- **Konkrete, umsetzbare** Empfehlungen geben
- **Niemals diagnostizierend** oder medizinisch verschreibend
- **Ermutigend und hoffnungsvoll** im Ton
- **Klar strukturiert** und praktisch hilfreich

## 📊 Beispiel-Prompts für spezielle Situationen:

### Mood Analysis Datensätze:
```
"Erstelle 50 realistische Mood-Einträge für junge Erwachsene (20-30) in verschiedenen Lebenskrisen wie Studienabschluss, erste Arbeitsstelle, Beziehungsprobleme und Zukunftsängste."

"Generiere 40 Mood-Tracking Samples für Menschen mit Depression in verschiedenen Behandlungsphasen - von akuter Episode bis hin zur Stabilisierung."

"Erstelle 60 diverse Mood-Einträge für Eltern mit verschiedenen Herausforderungen: Schlafmangel, Erziehungsstress, Schuldgefühle und positive Momente."
```

### Dream Analysis Datensätze:
```
"Generiere 30 Dream-Analysis Samples die kulturelle Traumsymbole aus verschiedenen Kulturen einbeziehen (europäisch, asiatisch, afrikanisch, lateinamerikanisch)."

"Erstelle 25 Alptraum-Analysen mit verschiedenen Angstthemen: Verfolgung, Fallen, Versagen, Verlust, Kontrollverlust."

"Generiere 40 Lucide Dream Samples mit verschiedenen Kontrollgraden und Bewusstseinsstufen im Traum."
```

### Therapy Notes Datensätze:
```
"Erstelle 40 Therapy Notes von Menschen mit Angststörungen in verschiedenen CBT-Behandlungsphasen."

"Generiere 30 Selbstreflexions-Einträge von Menschen, die DBT-Techniken erlernen und anwenden."

"Erstelle 35 Therapie-Session Notes für verschiedene Behandlungsansätze: CBT, DBT, EMDR, Gesprächstherapie."
```

## 🎯 Konkrete Anwendungsbeispiele:

### Beispiel 1: Balanced Mood Dataset
```
Erstelle 100 realistische Mood-Tracking Einträge:
- 20x Depression (mild bis schwer, verschiedene Auslöser)
- 20x Angststörungen (Panik, soziale Angst, generalisierte Angst)
- 20x Bipolare Episoden (manisch, depressiv, gemischt)
- 20x Burnout/Arbeitsstress (verschiedene Berufe und Situationen)
- 20x Normale Alltagsschwankungen (gesunde Baseline)

Achte auf:
- Authentische Sprache und verschiedene Bildungsgrade
- Kulturelle Vielfalt (deutsch, türkisch, arabisch, etc.)
- Altersgruppen von 18-65 Jahren
- Realistische Aktivitäten und Lebenssituationen
- Klinische Genauigkeit in den AI-Antworten
```

### Beispiel 2: Cultural Dream Dataset
```
Generiere 75 diverse Traumanalyse-Samples:
- 15x Angstträume (Verfolgung, Fallen, Versagen, Isolation)
- 15x Symbolreiche Träume (Tiere, Natur, Häuser, Wasser)
- 15x Beziehungsträume (Familie, Partner, Konflikte, Versöhnung)
- 15x Lucide Träume (verschiedene Kontrollgrade)
- 15x Wiederkehrende Traumthemen (childhood memories, unfinished business)

Berücksichtige:
- Traumsymbole aus verschiedenen Kulturen
- Generationsunterschiede in Träumen
- Geschlechtsspezifische Traumthemen
- Lebensphasen-spezifische Träume
- Professionelle jungianische und freudianische Deutungsansätze
```

### Beispiel 3: Therapy Progress Dataset
```
Erstelle 60 Therapy Notes Samples:
- 20x Erste Therapiestunden (Kennenlernen, Problemerkundung)
- 20x Mittlere Therapiephase (Techniken lernen, Fortschritte)
- 20x Therapieabschluss (Reflexion, Rückfallprävention)

Verschiedene Störungsbilder:
- Depression, Angst, Trauma, Sucht, Essstörungen
- Verschiedene Therapieformen: CBT, DBT, EMDR, Gesprächstherapie
- Realistische Therapieverläufe mit Rückschlägen und Fortschritten
```

## 🔍 Qualitätskontrolle-Checkliste:

### Für jeden Datensatz prüfen:
- [ ] **Realismus**: Klingen die Einträge wie echte Patientenaussagen?
- [ ] **Diversität**: Verschiedene Demografien repräsentiert?
- [ ] **Klinische Genauigkeit**: Medizinisch/psychologisch korrekt?
- [ ] **Sprachvariation**: Verschiedene Bildungsgrade und Altersgruppen?
- [ ] **Kulturelle Sensibilität**: Respektvoller Umgang mit verschiedenen Kulturen?
- [ ] **Datenschutz**: Keine identifizierbaren Informationen?
- [ ] **Ethik**: Keine stigmatisierenden oder diskriminierenden Inhalte?

## 📈 Upload-Format für MindBridge API:

### Standard Upload via POST /api/v1/ai-training/datasets/{id}/upload:
```json
{
  "type": "mood_analysis",
  "metadata": {
    "created_by": "AI_Generator",
    "creation_date": "2024-01-15",
    "version": "1.0",
    "description": "Diverse mood tracking samples for training",
    "total_samples": 100,
    "demographics": {
      "age_range": "18-65",
      "cultures": ["german", "turkish", "arabic", "eastern_european"],
      "conditions": ["depression", "anxiety", "bipolar", "healthy_baseline"]
    }
  },
  "samples": [
    // Hier die generierten Samples einfügen
  ]
}
```

## 🚀 Produktive Nutzung:

### Schritt 1: Dataset erstellen
```bash
POST /api/v1/ai-training/datasets
{
  "name": "Mood Analysis Training Set v1.0",
  "description": "Comprehensive mood tracking training data",
  "dataset_type": "mood_analysis",
  "data_format": "json"
}
```

### Schritt 2: Trainingsdaten hochladen
```bash
POST /api/v1/ai-training/datasets/{dataset_id}/upload
# JSON Daten aus AI-Generation
```

### Schritt 3: Model Training starten
```bash
POST /api/v1/ai-training/models/train
{
  "model_name": "MoodClassifier_v1.0",
  "model_type": "mood_classifier",
  "dataset_ids": ["{dataset_id}"]
}
```

## 💡 Pro-Tips für bessere Trainingsdaten:

1. **Iterative Verbesserung**: Starte mit kleineren Sets und verfeinere basierend auf Model Performance
2. **Balancierte Datensätze**: Gleiche Anzahl verschiedener Kategorien für bessere Genauigkeit
3. **Edge Cases einbeziehen**: Ungewöhnliche aber realistische Situationen
4. **Feedback Loop**: Model-Predictions evaluieren und Trainingsdaten entsprechend anpassen
5. **Kontinuierliche Updates**: Regelmäßig neue Daten hinzufügen um Model Performance zu erhalten

---

**Mit diesem Guide kannst du hochwertige, diverse und klinisch fundierte Trainingsdaten für deine MindBridge AI Platform generieren! 🎯**
```

Bitte erstelle jetzt [SPEZIFISCHE ANFRAGE] und achte dabei besonders auf [FOKUSBEREICH].

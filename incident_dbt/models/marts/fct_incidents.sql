{{ config(materialized='table') }}

with base as (
  select * from {{ ref('stg_uci_incident_events') }}
),

-- one row per incident_id
per_incident as (
  select
    number                                      as incident_id,
    min(opened_at)                              as opened_at,
    min(sys_created_at)                         as created_at,
    min(resolved_at)                            as first_resolved_at,
    min(closed_at)                              as closed_at,
    max(incident_state)                         as last_state,
    max(priority)                               as priority,
    max(impact)                                 as impact,
    max(urgency)                                as urgency,
    -- pick a representative value for descriptive fields
    max(category)                               as category,
    max(subcategory)                            as subcategory,
    max(assignment_group)                       as assignment_group,
    bool_or(made_sla)                           as made_sla 
  from base
  group by number
),

metrics as (
  select
    *,
    extract(epoch from (created_at - opened_at))/3600.0                                         as mttd_hours,
    extract(epoch from (first_resolved_at - opened_at))/3600.0                                   as mttr_hours,
    case
      when priority = 1 and (extract(epoch from (first_resolved_at - opened_at))/3600.0) <= 4  then true
      when priority = 2 and (extract(epoch from (first_resolved_at - opened_at))/3600.0) <= 8  then true
      when priority >= 3 and (extract(epoch from (first_resolved_at - opened_at))/3600.0) <= 24 then true
      else false
    end                                                                                           as sla_met_by_priority
  from per_incident
)
select * from metrics

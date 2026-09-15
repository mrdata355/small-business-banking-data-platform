# Databricks notebook source
# MAGIC %md
# MAGIC # Contract Genome / Change Blast Radius
# MAGIC Compare a proposed data contract with the current contract before promotion.

# COMMAND ----------
from dataclasses import replace
from digital_twin.contract_genome import ContractChange, default_contract_graph

# COMMAND ----------
graph = default_contract_graph()
current = graph.contracts['silver_lending.loan_application']
print('current genome:', current.genome)

# COMMAND ----------
# Example additive change: nullable analyst_note field.
proposed = replace(
    current,
    version='1.1.0',
    fields=current.fields + (('analyst_note', 'string', True),),
)
result = graph.evaluate(ContractChange(current.asset, current, proposed))
display([{
    'asset': result.changed_asset,
    'compatibility': result.compatibility,
    'estimated_risk': result.estimated_risk,
    'directly_impacted': ','.join(result.directly_impacted),
    'transitively_impacted': ','.join(result.transitively_impacted),
    'reasons': '; '.join(result.reasons),
}])

# COMMAND ----------
# Example breaking change: changing the business key.
breaking = replace(current, version='2.0.0', business_keys=('application_id','event_version'))
breaking_result = graph.evaluate(ContractChange(current.asset, current, breaking))
display([{
    'compatibility': breaking_result.compatibility,
    'estimated_risk': breaking_result.estimated_risk,
    'critical_paths': breaking_result.critical_paths,
}])

"""Operational donor/request metrics with no donor identity in aggregates."""
from collections import Counter


def summarize_requests(rows):
    urgency = Counter((r.get('urgency') or 'normal') for r in rows)
    groups = Counter((r.get('blood_group') or 'unknown') for r in rows)
    return {
        'total_requests': len(rows),
        'critical_requests': urgency.get('critical', 0),
        'high_requests': urgency.get('high', 0),
        'normal_requests': urgency.get('normal', 0),
        'blood_group_demand': dict(sorted(groups.items())),
    }


def summarize_interactions(rows):
    total = len(rows)
    accepted = sum(r.get('response') == 'accepted' for r in rows)
    completed = sum(r.get('response') == 'completed' for r in rows)
    declined = sum(r.get('response') == 'declined' for r in rows)
    no_response = sum(r.get('response') == 'no_response' for r in rows)
    probabilities = [float(r['predicted_probability']) for r in rows if r.get('predicted_probability') is not None]
    return {
        'total_contacts': total,
        'accepted': accepted,
        'completed': completed,
        'declined': declined,
        'no_response': no_response,
        'acceptance_rate': round(accepted / total, 4) if total else 0.0,
        'completion_rate': round(completed / accepted, 4) if accepted else 0.0,
        'mean_predicted_probability': round(sum(probabilities) / len(probabilities), 4) if probabilities else None,
    }

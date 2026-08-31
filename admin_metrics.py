"""Privacy-conscious operational metrics for administrators."""


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

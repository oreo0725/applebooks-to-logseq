- author:: [[{{ author }}]]
- full-title:: "{{ title }}"
- category:: #books
- tags:: #[[reading]]
- Highlights first synced by [[{{ sync_date }}]]
{% for highlight in highlights %}
  - > {{ highlight.text }}{% if highlight.page %} (Page {{ highlight.page }}){% endif %}
    {% if highlight.note %}- Note:: {{ highlight.note }}{% endif %}
{% endfor %}

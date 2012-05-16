# -*- coding: utf-8 -*-

from ladon.compat import PORTABLE_STRING

catalog_default_template = PORTABLE_STRING("""
<html>
	<head>
		<meta content="text/html; charset={{ charset }}" http-equiv="Content-Type" />
		<title>{{ catalog_name }}</title>
		<style>
{{ css }}
		</style>
	</head>
	<body>
		<div class="catName">{{ catalog_name }}</div>
		<div class="catDesc">{{ catalog_desc }}</div>
		<div class="catContent">
			<ul class="catService">
{% for service in services %}
				<li>
					<b><a href="{{ client_path }}/{{ service.servicename }}{{ '?' if query_string }}{{query_string}}">{{ service.servicename }}</a></b><br/>
					{{ service.doc_lines|join('\\n') }}
				</li>
{% endfor %}
			</ul>
		</div>
		<div class="catGen">Powered by Ladon for Python</div>
	</body>
</html>
""")

service_default_template = PORTABLE_STRING("""
<html>
	<head>
		<meta content="text/html; charset={{ charset }}" http-equiv="Content-Type" />
		<title>{{ servicename }}</title>
		<style>
{{ css }}
		</style>
	</head>
	<body>
		<div class="service-header">
			<div class="service-title">{{ servicename }}</div>
			<form method="get" class="skin-selector">
				<label for="skin-select">skins:</label>
				<select id="skin-select" name="skin" onchange="document.forms[0].submit()">
					<option value="">Default</option>
					{% for skin in skins %}
					<option value="{{skin}}"{% if skin == current_skin %} selected{% endif %}>{{ skin|title }}</option>
					{% endfor %}
				</select>
			</form>
		</div>
		<div class="service-overview">
			<div class="headline">Overview</div>
			<div class="title">Methods</div>
			<ul class="list">
{% for method in methods %}
				<li>
					<a href="#{{ method.methodname }}"><span class="entry">{{ method.methodname }}</span></a>
					( )
				</li>
{% endfor %}
			</ul>
			<div class="title">Types</div>
			<ul class="list">
{% for type in types %}
				<li>
					<a href="#{{ type.name }}"><span class="entry">{{ type.name }}</span></a>
				</li>
{% endfor %}
			</ul>
		</div>

		<div class="service-description">
			<div class="title">Description</div>
			<p class="doc-lines">
				{{ doc_lines|join('\\n') }}
			</p>
		</div>
		<div class="service-interfaces">
			<div class="title">Interfaces</div>
			<ul class="list">
{% for interface in interfaces %}
				<li>{{ interface }} [ <a href="{{ client_path }}/{{ interface }}">url</a> <a href="{{ client_path }}/{{ interface }}/description">description</a> ]</li>
{% endfor %}
			</ul>
		</div>
		<div class="service-api">
			<div class="methods">
				<div class="title">Methods</div>
				<ul class="list">
	{% for method in methods %}
					<li class="entry">
						<div class="declaration">
							<a name="{{ method.methodname }}"></a><span class="name">{{ method.methodname }}</span>
							(
		{% set sep = '' %}
		{% for param in method.params %}
							{{ sep }} 
							<span class="param-type">
			{% if param.ladontype %}
								<a href="#{{ param.ladontype }}">{{ param.type }}</a>
			{% else %}
								{{ param.type }}
			{% endif %}
							</span> 
							<span class="param-name">{{ param.name }}</span>
			{% set sep = ',' %}
		{% endfor %}
							)
						</div>
						<p class="doc-lines">
							{{ method.doc_lines|join('\\n') }}
						</p>
		{% for param in method.params %}
			{% if loop.first %}
						<div class="params-title">Parameters</div>
						<ul class="params">
			{% endif %}
							<li>
								<span class="param-name">{{ param.name }}</span>: <span class="param-type">
			{% if param.ladontype %}
									<a href="#{{ param.ladontype }}">{{ param.type }}</a>
			{% else %}
									{{ param.type }}
			{% endif %}
								</span>
			{% if param.optional %}
								[ default: {{ param.default }} ]
			{% endif %}
								<br/>
								<p class="doc-lines">
									{{ param.doc_lines|join('\\n') }}
								</p>
							</li> 
			{% if loop.last %}
						</ul>
			{% endif %}
		{% endfor %}
						<div class="return-type-title">Return value</div>
						<div class="return-type">
							<span class="param-type">
		{% if method.returns.ladontype %}
								<a href="#{{ method.returns.ladontype }}">{{ method.returns.type }}</a>
		{% else %}
								{{ method.returns.type }}
		{% endif %}
							</span>
							<p class="doc-lines">
								{{ method.returns.doc_lines|join('\\n') }}
							</p>
						</div>
					</li>
	{% endfor %}
				</ul>
			</div>
			<div class="types">
				<div class="title">Types</div>
				<ul class="list">
	{% for type in types %}
					<li class="entry">
						<div class="definition">
							<a name="{{ type.name }}"></a><span class="name">{{ type.name }}</span>
						</div>
						<div class="attributes-title">Attributes</div>
						<ul class="attributes">
		{% for k,v in type.attributes.items() %}
							<li>
								<span class="param-name">{{ k }}</span>:
								<span class="param-type">
			{% if v.ladontype %}
									<a href="#{{v.ladontype}}">{{ v.type }}</a>
			{% else %}
									{{ v.type }}
			{% endif %}
								</span>
			{% set prefix = '[' %}
			{% set suffix = '' %}
			{% if 'nullable' in v.props and v.props.nullable==True %}
								{{ prefix }} Nullable
				{% set prefix = ' |' %}
				{% set suffix = ' ]' %}
			{% endif %}
			{% if 'default' in v.props %}
								{{ prefix }} default: {{ v.props.default }}
				{% set prefix = ' | ' %}
				{% set suffix = ' ]' %}
			{% endif %}
			{{ suffix }}
			{% if 'doc' in v.props %}
								<br/>
								<p class="doc-lines">
									{{ v.props.doc|join('\\n') }}
								</p>
			{% endif %}
							</li>
		{% endfor %}
						</ul>
					</li>
	{% endfor %}
				</ul>
			</div>
		</div>
		<div class="service-footer">Powered by Ladon for Python</div>
	</body>
</html>
""")

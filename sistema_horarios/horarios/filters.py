from django.db.models import Q


def build_filter_qs(request):
    params = request.GET.copy()
    params.pop('page', None)
    return params.urlencode()


def count_active_filters(request, list_keys=None, text_key='q'):
    count = 0
    if request.GET.get(text_key, '').strip():
        count += 1
    for key in list_keys or []:
        if request.GET.get(key, '').strip():
            count += 1
    return count


def filter_titulaciones(queryset, request):
    q = request.GET.get('q', '').strip()
    if q:
        queryset = queryset.filter(Q(codigo__icontains=q) | Q(nombre__icontains=q))
    return queryset


def filter_asignaturas(queryset, request):
    q = request.GET.get('q', '').strip()
    titulacion = request.GET.get('titulacion', '').strip()
    curso = request.GET.get('curso', '').strip()
    tipo = request.GET.get('tipo', '').strip()

    if q:
        queryset = queryset.filter(
            Q(codigo__icontains=q)
            | Q(nombre__icontains=q)
            | Q(profesor__nombre__icontains=q)
            | Q(profesor__apellidos__icontains=q)
        )
    if titulacion:
        queryset = queryset.filter(titulacion_id=titulacion)
    if curso:
        queryset = queryset.filter(curso=curso)
    if tipo == 'electiva':
        queryset = queryset.filter(es_electiva=True)
    elif tipo == 'obligatoria':
        queryset = queryset.filter(es_electiva=False)

    return queryset.distinct()


def filter_profesores(queryset, request):
    q = request.GET.get('q', '').strip()
    titulacion = request.GET.get('titulacion', '').strip()

    if q:
        queryset = queryset.filter(
            Q(nombre__icontains=q)
            | Q(apellidos__icontains=q)
            | Q(email__icontains=q)
            | Q(asignaturas__codigo__icontains=q)
            | Q(asignaturas__nombre__icontains=q)
        )
    if titulacion:
        queryset = queryset.filter(asignaturas__titulacion_id=titulacion)

    return queryset.distinct()


def filter_sesiones(queryset, request):
    q = request.GET.get('q', '').strip()
    dia = request.GET.get('dia', '').strip()
    titulacion = request.GET.get('titulacion', '').strip()

    if q:
        queryset = queryset.filter(
            Q(asignatura__codigo__icontains=q)
            | Q(asignatura__nombre__icontains=q)
        )
    if dia:
        queryset = queryset.filter(dia=dia)
    if titulacion:
        queryset = queryset.filter(asignatura__titulacion_id=titulacion)

    return queryset.distinct()

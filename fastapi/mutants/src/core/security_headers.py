# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut: MutantDict = {}  # type: ignore


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    @_mutmut_mutated(mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut)
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_orig(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_1(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = None

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_2(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(None)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_3(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = None
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_4(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["XXX-Content-Type-OptionsXX"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_5(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["x-content-type-options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_6(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-CONTENT-TYPE-OPTIONS"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_7(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "XXnosniffXX"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_8(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "NOSNIFF"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_9(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = None
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_10(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["XXX-Frame-OptionsXX"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_11(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["x-frame-options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_12(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-FRAME-OPTIONS"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_13(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "XXDENYXX"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_14(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "deny"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_15(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = None
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_16(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["XXReferrer-PolicyXX"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_17(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["referrer-policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_18(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["REFERRER-POLICY"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_19(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "XXstrict-origin-when-cross-originXX"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_20(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "STRICT-ORIGIN-WHEN-CROSS-ORIGIN"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_21(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = None
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_22(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["XXPermissions-PolicyXX"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_23(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["permissions-policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_24(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["PERMISSIONS-POLICY"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_25(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "XXgeolocation=(), camera=(), microphone=()XX"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_26(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "GEOLOCATION=(), CAMERA=(), MICROPHONE=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_27(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = None

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_28(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["XXContent-Security-PolicyXX"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_29(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["content-security-policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_30(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["CONTENT-SECURITY-POLICY"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_31(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "XXdefault-src 'none'; frame-ancestors 'none'; sandboxXX"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_32(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "DEFAULT-SRC 'NONE'; FRAME-ANCESTORS 'NONE'; SANDBOX"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_33(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith(None):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_34(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("XX/api/XX"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_35(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/API/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_36(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = None
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_37(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["XXCache-ControlXX"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_38(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["cache-control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_39(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["CACHE-CONTROL"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_40(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "XXno-store, no-cache, must-revalidate, max-age=0XX"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_41(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "NO-STORE, NO-CACHE, MUST-REVALIDATE, MAX-AGE=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_42(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = None

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_43(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["XXPragmaXX"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_44(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_45(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["PRAGMA"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_46(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "XXno-cacheXX"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_47(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "NO-CACHE"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_48(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = None

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_49(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["XXServerXX"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_50(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["server"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_51(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["SERVER"] = "RoSGrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_52(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "XXRoSGridXX"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_53(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "rosgrid"

        return response
    async def xǁSecurityHeadersMiddlewareǁdispatch__mutmut_54(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "ROSGRID"

        return response

mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['_mutmut_orig'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_orig # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_1'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_1 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_2'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_2 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_3'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_3 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_4'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_4 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_5'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_5 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_6'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_6 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_7'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_7 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_8'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_8 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_9'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_9 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_10'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_10 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_11'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_11 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_12'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_12 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_13'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_13 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_14'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_14 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_15'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_15 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_16'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_16 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_17'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_17 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_18'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_18 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_19'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_19 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_20'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_20 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_21'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_21 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_22'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_22 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_23'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_23 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_24'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_24 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_25'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_25 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_26'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_26 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_27'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_27 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_28'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_28 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_29'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_29 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_30'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_30 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_31'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_31 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_32'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_32 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_33'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_33 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_34'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_34 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_35'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_35 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_36'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_36 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_37'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_37 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_38'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_38 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_39'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_39 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_40'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_40 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_41'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_41 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_42'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_42 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_43'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_43 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_44'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_44 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_45'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_45 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_46'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_46 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_47'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_47 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_48'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_48 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_49'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_49 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_50'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_50 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_51'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_51 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_52'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_52 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_53'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_53 # type: ignore # mutmut generated
mutants_xǁSecurityHeadersMiddlewareǁdispatch__mutmut['xǁSecurityHeadersMiddlewareǁdispatch__mutmut_54'] = SecurityHeadersMiddleware.xǁSecurityHeadersMiddlewareǁdispatch__mutmut_54 # type: ignore # mutmut generated
